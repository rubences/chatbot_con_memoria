"""Orquestador ReWOO para analisis de transcripciones de call center.

ReWOO separa el flujo en tres modulos:
1) Planificador: descompone la tarea en subpreguntas.
2) Trabajador: recupera evidencia (RAG local y web opcional) y responde cada subpregunta.
3) Solucionador: sintetiza una respuesta final estructurada.
"""

from __future__ import annotations

import logging
import os
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
        self._cliente = OpenAI(
            api_key=clave_api,
            **({"base_url": obtener_url_base()} if obtener_url_base() else {}),
        )

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
        """Genera texto con el modelo configurado."""
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
        except OpenAIError as error:
            logger.error("Error LLM en ReWOO: %s", error)
            raise RuntimeError(f"Fallo al generar respuesta ReWOO: {error}") from error

        return (respuesta.choices[0].message.content or "").strip()

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
