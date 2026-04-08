"""Orquestador ReWOO para analisis de transcripciones de call center.

ReWOO separa el flujo en tres modulos:
1) Planificador: descompone la tarea en subpreguntas.
2) Trabajador: recupera evidencia (RAG local y web opcional) y responde cada subpregunta.
3) Solucionador: sintetiza una respuesta final estructurada.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

import requests
from openai import OpenAI, OpenAIError

from chat_agentes.agentes import AgenteRAG, ErrorConfiguracionModelo, FragmentoRAG
from src.config import (
    clave_api_parece_placeholder,
    obtener_clave_api,
    obtener_modelo,
    obtener_temperatura,
    obtener_url_base,
)

logger = logging.getLogger(__name__)


@dataclass
class ResultadoReWOO:
    """Resultado completo del pipeline ReWOO."""

    plan: list[str]
    respuestas: dict[str, str]
    resumen_final: str
    informe_markdown: str


class OrquestadorReWOOAnalisis:
    """Ejecutor ReWOO para analisis de llamadas de atencion al cliente."""

    def __init__(self, usar_busqueda_web: bool = False) -> None:
        self.usar_busqueda_web = usar_busqueda_web
        self._rag = AgenteRAG()

        clave_api = obtener_clave_api()
        if clave_api_parece_placeholder(clave_api):
            raise ErrorConfiguracionModelo(
                "La clave API no es valida para ejecutar ReWOO. "
                "Revisa OPENAI_API_KEY o HF_API_KEY en .env."
            )

        self._modelo = obtener_modelo()
        self._temperatura = obtener_temperatura()
        self._max_reintentos_429 = max(0, int(os.getenv("REWOO_MAX_REINTENTOS_429", "3")))
        self._backoff_inicial_segundos = max(
            0.2,
            float(os.getenv("REWOO_BACKOFF_INICIAL_SEGUNDOS", "1.5")),
        )
        self._cliente = OpenAI(
            api_key=clave_api,
            **({"base_url": obtener_url_base()} if obtener_url_base() else {}),
        )

    @staticmethod
    def _es_error_rate_limit(mensaje_error: str) -> bool:
        """Determina si el error corresponde a límite de tasa (429)."""
        texto = mensaje_error.lower()
        return "429" in texto or "rate-limited" in texto or "rate limit" in texto

    def planificador(self, transcripcion: str) -> list[str]:
        """Genera subpreguntas especializadas para la transcripcion."""
        if not transcripcion.strip():
            return []

        return [
            "Cual es el resumen factual de la llamada y sus hitos principales?",
            "Que indicadores de escalada y riesgo reputacional aparecen en la interaccion?",
            "Como fue la calidad del agente segun empatia, tono, resolucion y profesionalismo?",
            "Que recomendaciones concretas debe ejecutar un manager de call center?",
        ]

    def _consultar_serper(self, pregunta: str, max_resultados: int = 3) -> str:
        """Recupera snippets de Serper.dev cuando hay API key disponible."""
        api_key = os.getenv("SERPER_API_KEY", "").strip()
        if not api_key:
            return ""

        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": api_key,
                    "Content-Type": "application/json",
                },
                json={"q": pregunta, "num": max_resultados},
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
            snippets = [item.get("snippet", "") for item in data.get("organic", [])]
            return "\n".join([s for s in snippets if s.strip()])
        except (requests.RequestException, ValueError) as error:
            logger.warning("Busqueda web ReWOO no disponible: %s", error)
            return ""

    def _generar_texto(self, prompt: str) -> str:
        """Genera texto con el modelo configurado y retry exponencial para 429."""
        intentos_totales = self._max_reintentos_429 + 1

        for intento in range(1, intentos_totales + 1):
            try:
                respuesta = self._cliente.chat.completions.create(
                    model=self._modelo,
                    temperature=self._temperatura,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Eres un analista de calidad de call center. "
                                "Responde de forma clara, concreta y basada en evidencia."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                return (respuesta.choices[0].message.content or "").strip()
            except OpenAIError as error:
                mensaje = str(error)
                logger.error("Error LLM en ReWOO (intento %d/%d): %s", intento, intentos_totales, mensaje)

                # Mensajes más claros para proveedores OpenAI-compatible (OpenRouter incluido).
                if "402" in mensaje or "Insufficient credits" in mensaje:
                    raise ErrorConfiguracionModelo(
                        "El proveedor no tiene créditos suficientes para el modelo actual. "
                        "Usa un modelo gratuito (:free) o recarga créditos."
                    ) from error
                if "404" in mensaje or "No endpoints found" in mensaje:
                    raise ErrorConfiguracionModelo(
                        "El modelo configurado no existe o no está disponible en el proveedor. "
                        "Revisa la variable MODELO en .env."
                    ) from error

                # Retry exponencial solo para rate-limit.
                if self._es_error_rate_limit(mensaje) and intento < intentos_totales:
                    espera = self._backoff_inicial_segundos * (2 ** (intento - 1))
                    logger.warning(
                        "Rate-limit detectado; reintentando en %.1f s (intento %d/%d).",
                        espera,
                        intento + 1,
                        intentos_totales,
                    )
                    time.sleep(espera)
                    continue

                if self._es_error_rate_limit(mensaje):
                    raise RuntimeError(
                        "El modelo está temporalmente limitado por tasa (429). "
                        "Se agotaron los reintentos automáticos; intenta de nuevo en unos segundos o cambia de modelo."
                    ) from error

                raise RuntimeError(f"Fallo al generar respuesta ReWOO: {mensaje}") from error

        # No debería alcanzarse por el control de flujo anterior.
        raise RuntimeError("No se pudo generar texto en ReWOO.")

    def trabajador(self, subpregunta: str, transcripcion: str) -> str:
        """Resuelve una subpregunta con evidencia RAG y web opcional."""
        fragmentos: list[FragmentoRAG] = self._rag.buscar(subpregunta, max_resultados=3)
        evidencia_rag = "\n\n".join(
            [
                f"Fuente: {f.fuente}\nPuntaje: {f.puntaje:.2f}\nContenido: {f.contenido}"
                for f in fragmentos
            ]
        )
        evidencia_web = self._consultar_serper(subpregunta) if self.usar_busqueda_web else ""

        prompt = (
            "Responde la subpregunta usando solo la evidencia disponible. "
            "Si una parte no esta en la evidencia, dilo explicitamente.\n\n"
            f"Subpregunta:\n{subpregunta}\n\n"
            f"Transcripcion:\n{transcripcion}\n\n"
            f"Evidencia RAG:\n{evidencia_rag or 'Sin evidencia RAG adicional.'}\n\n"
            f"Evidencia web:\n{evidencia_web or 'No usada.'}\n\n"
            "Respuesta (6-10 lineas, precisa y accionable):"
        )
        return self._generar_texto(prompt)

    def solucionador(self, transcripcion: str, respuestas: dict[str, str]) -> str:
        """Sintetiza la salida final a partir de las subrespuestas."""
        bloque_respuestas = "\n\n".join(
            [f"Subpregunta: {pregunta}\nRespuesta: {respuesta}" for pregunta, respuesta in respuestas.items()]
        )

        prompt = (
            "Genera un informe final en Markdown para lideres de atencion al cliente, "
            "con secciones: Resumen Ejecutivo, Hallazgos, Riesgos de Escalada, "
            "Evaluacion de Calidad y Plan de Accion.\n\n"
            f"Transcripcion original:\n{transcripcion}\n\n"
            f"Respuestas parciales del pipeline ReWOO:\n{bloque_respuestas}\n\n"
            "Entrega recomendaciones concretas priorizadas (inmediatas, corto plazo, estrategicas)."
        )
        return self._generar_texto(prompt)

    def analizar(self, transcripcion: str) -> ResultadoReWOO:
        """Ejecuta el pipeline completo de ReWOO sobre la transcripcion."""
        transcripcion = transcripcion.strip()
        if not transcripcion:
            raise ValueError("La transcripcion no puede estar vacia.")

        plan = self.planificador(transcripcion)
        respuestas: dict[str, str] = {}
        for subpregunta in plan:
            respuestas[subpregunta] = self.trabajador(subpregunta, transcripcion)

        resumen_final = self.solucionador(transcripcion, respuestas)

        seccion_plan = "\n".join([f"- {p}" for p in plan])
        seccion_subrespuestas = "\n\n".join(
            [f"### {i}. {p}\n{r}" for i, (p, r) in enumerate(respuestas.items(), start=1)]
        )
        informe_markdown = (
            "# Informe ReWOO\n\n"
            "## Planificador\n"
            f"{seccion_plan}\n\n"
            "## Trabajador\n"
            f"{seccion_subrespuestas}\n\n"
            "## Solucionador\n"
            f"{resumen_final}\n"
        )

        return ResultadoReWOO(
            plan=plan,
            respuestas=respuestas,
            resumen_final=resumen_final,
            informe_markdown=informe_markdown,
        )
