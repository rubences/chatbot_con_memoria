"""Agentes especializados y orquestador del chatbot."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI, OpenAIError

from chat_agentes.models import Conversacion, Mensaje
from src.config import (
    clave_api_parece_placeholder,
    obtener_clave_api,
    obtener_mensaje_sistema,
    obtener_modelo,
    obtener_proveedor,
    obtener_url_base,
)

logger = logging.getLogger(__name__)


@dataclass
class FragmentoRAG:
    """Fragmento recuperado del repositorio de conocimiento."""

    fuente: str
    contenido: str
    puntaje: float


class ErrorConfiguracionModelo(ValueError):
    """Se lanza cuando la configuración del proveedor es inválida."""


class AgenteModelo:
    """Se encarga exclusivamente de hablar con el modelo LLM."""

    def __init__(self) -> None:
        self.proveedor = obtener_proveedor()
        self.clave_api = obtener_clave_api()
        self.modelo = obtener_modelo()
        self.url_base = obtener_url_base()

        if clave_api_parece_placeholder(self.clave_api):
            raise ErrorConfiguracionModelo(
                "La clave API no es válida. Revisa OPENAI_API_KEY o HF_API_KEY en el archivo .env."
            )

        self._cliente = OpenAI(
            api_key=self.clave_api,
            **({"base_url": self.url_base} if self.url_base else {}),
        )

    def generar_respuesta(
        self,
        historial: list[dict[str, str]],
        instrucciones_agente: str,
        contexto_rag: list[FragmentoRAG],
    ) -> str:
        """Genera la respuesta del asistente con instrucciones de agente y RAG."""
        mensajes = list(historial)

        if mensajes and mensajes[0]["role"] == "system":
            mensajes[0]["content"] = (
                f"{mensajes[0]['content']}\n\n"
                f"[Instrucciones de agente experto]\n{instrucciones_agente}"
            )

        if contexto_rag:
            bloques = []
            for fragmento in contexto_rag:
                bloques.append(
                    f"Fuente: {fragmento.fuente}\n"
                    f"Puntaje: {fragmento.puntaje:.2f}\n"
                    f"Contenido:\n{fragmento.contenido}"
                )
            mensajes.append(
                {
                    "role": "system",
                    "content": (
                        "Usa este contexto RAG solo cuando sea relevante y cita la fuente "
                        "por su nombre de archivo entre paréntesis.\n\n"
                        + "\n\n---\n\n".join(bloques)
                    ),
                }
            )

        try:
            respuesta = self._cliente.chat.completions.create(
                model=self.modelo,
                messages=mensajes,
            )
        except OpenAIError as error:
            logger.error("Fallo al invocar el modelo: %s", error)
            raise

        contenido = respuesta.choices[0].message.content or ""
        return contenido.strip()

    async def generar_respuesta_async(
        self,
        historial: list[dict[str, str]],
        instrucciones_agente: str,
        contexto_rag: list[FragmentoRAG],
    ) -> str:
        """Versión asíncrona que ejecuta la llamada bloqueante en un hilo."""
        return await asyncio.to_thread(
            self.generar_respuesta,
            historial,
            instrucciones_agente,
            contexto_rag,
        )


class AgenteVista:
    """Transforma el dominio persistido en contexto consumible por Django."""

    def construir_contexto(
        self,
        conversacion: Conversacion,
        agentes_activados: list[str] | None = None,
        fuentes_rag: list[str] | None = None,
    ) -> dict[str, Any]:
        mensajes = [
            {
                "rol": mensaje.rol,
                "contenido": mensaje.contenido,
                "orden": mensaje.orden,
            }
            for mensaje in conversacion.mensajes.exclude(rol=Mensaje.Roles.SISTEMA)
        ]
        return {
            "conversacion_id": conversacion.id,
            "titulo": conversacion.titulo,
            "mensajes": mensajes,
            "proveedor": obtener_proveedor(),
            "modelo": obtener_modelo(),
            "agentes_activados": agentes_activados or [],
            "fuentes_rag": fuentes_rag or [],
        }


class AgenteRAG:
    """Recupera fragmentos relevantes desde archivos locales de conocimiento."""

    def __init__(self, ruta_base: Path | None = None) -> None:
        base_por_defecto = Path(__file__).parent / "conocimiento"
        self.ruta_base = ruta_base or base_por_defecto
        self.extensiones = {".md", ".txt", ".rst", ".py"}

    def buscar(self, consulta: str, max_resultados: int = 3) -> list[FragmentoRAG]:
        if not self.ruta_base.exists():
            return []

        tokens_consulta = self._tokenizar(consulta)
        if not tokens_consulta:
            return []

        resultados: list[FragmentoRAG] = []
        for archivo in self.ruta_base.rglob("*"):
            if not archivo.is_file() or archivo.suffix.lower() not in self.extensiones:
                continue

            try:
                contenido = archivo.read_text(encoding="utf-8")
            except OSError:
                continue

            tokens_archivo = self._tokenizar(contenido)
            if not tokens_archivo:
                continue

            interseccion = tokens_consulta.intersection(tokens_archivo)
            if not interseccion:
                continue

            puntaje = len(interseccion) / max(len(tokens_consulta), 1)
            fragmento = contenido[:900].strip()
            resultados.append(
                FragmentoRAG(
                    fuente=archivo.name,
                    contenido=fragmento,
                    puntaje=puntaje,
                )
            )

        resultados.sort(key=lambda item: item.puntaje, reverse=True)
        return resultados[:max_resultados]

    @staticmethod
    def _tokenizar(texto: str) -> set[str]:
        return {token.lower() for token in re.findall(r"[a-zA-Z0-9_áéíóúñÁÉÍÓÚÑ]{3,}", texto)}


class AgenteEnrutadorTematico:
    """Selecciona uno o varios agentes expertos según el contexto."""

    TEMAS = {
        "python": {
            "palabras": {
                "python", "funcion", "funciones", "lista", "listas", "diccionario",
                "diccionarios", "pytest", "pep8", "clase", "clases", "tipado",
            },
            "instrucciones": (
                "Eres el Agente Python. Responde con enfoque práctico, ejemplos cortos y "
                "buenas prácticas de legibilidad y tipado."
            ),
        },
        "django": {
            "palabras": {
                "django", "vista", "vistas", "template", "orm", "modelo", "modelos",
                "migracion", "migraciones", "admin", "url", "urls", "csrf",
            },
            "instrucciones": (
                "Eres el Agente Django. Prioriza patrones MVC de Django, ORM, seguridad y "
                "estructura de apps."
            ),
        },
        "ia": {
            "palabras": {
                "llm", "rag", "prompt", "embeddings", "token", "inferencia", "modelo",
                "transformer", "agente", "agentes", "orquestador", "hallucination",
            },
            "instrucciones": (
                "Eres el Agente IA. Enfócate en diseño de prompts, RAG, enrutamiento y "
                "calidad de respuesta con criterios verificables."
            ),
        },
    }

    INSTRUCCIONES_GENERAL = (
        "Eres el Agente Generalista. Responde de forma clara y pide precisión solo cuando "
        "sea indispensable."
    )

    def seleccionar_agentes(
        self,
        mensaje: str,
        contexto_rag: list[FragmentoRAG],
    ) -> list[str]:
        tokens = AgenteRAG._tokenizar(mensaje)
        puntajes = {tema: 0 for tema in self.TEMAS}

        for tema, datos in self.TEMAS.items():
            puntajes[tema] += len(tokens.intersection(datos["palabras"]))

        for fragmento in contexto_rag:
            tokens_fragmento = AgenteRAG._tokenizar(fragmento.contenido)
            for tema, datos in self.TEMAS.items():
                if tokens_fragmento.intersection(datos["palabras"]):
                    puntajes[tema] += 1

        ordenados = sorted(puntajes.items(), key=lambda item: item[1], reverse=True)
        if not ordenados or ordenados[0][1] == 0:
            return ["general"]

        tema_top, puntaje_top = ordenados[0]
        seleccionados = [tema_top]

        for tema, puntaje in ordenados[1:]:
            if puntaje > 0 and puntaje >= max(1, int(puntaje_top * 0.6)):
                seleccionados.append(tema)

        return seleccionados[:3]

    def instrucciones_para(self, agente: str) -> str:
        if agente == "general":
            return self.INSTRUCCIONES_GENERAL
        return self.TEMAS[agente]["instrucciones"]


class AgenteControlador:
    """Gestiona la persistencia y el estado transaccional de la conversación."""

    def obtener_o_crear_conversacion(self, identificador_sesion: str) -> Conversacion:
        conversacion, creada = Conversacion.objects.get_or_create(
            identificador_sesion=identificador_sesion,
            defaults={
                "titulo": "Nueva conversación",
                "mensaje_sistema": obtener_mensaje_sistema(),
            },
        )

        if creada:
            self._crear_mensaje(
                conversacion=conversacion,
                rol=Mensaje.Roles.SISTEMA,
                contenido=conversacion.mensaje_sistema,
            )

        return conversacion

    def registrar_mensaje_usuario(self, conversacion: Conversacion, contenido: str) -> Mensaje:
        if conversacion.titulo == "Nueva conversación":
            conversacion.titulo = contenido[:60] or conversacion.titulo
            conversacion.save(update_fields=["titulo", "actualizada_en"])

        return self._crear_mensaje(
            conversacion=conversacion,
            rol=Mensaje.Roles.USUARIO,
            contenido=contenido,
        )

    def registrar_mensaje_asistente(self, conversacion: Conversacion, contenido: str) -> Mensaje:
        return self._crear_mensaje(
            conversacion=conversacion,
            rol=Mensaje.Roles.ASISTENTE,
            contenido=contenido,
        )

    def construir_historial_modelo(self, conversacion: Conversacion) -> list[dict[str, str]]:
        return [
            {"role": mensaje.rol, "content": mensaje.contenido}
            for mensaje in conversacion.mensajes.all()
        ]

    def _crear_mensaje(
        self,
        conversacion: Conversacion,
        rol: str,
        contenido: str,
    ) -> Mensaje:
        siguiente_orden = conversacion.mensajes.count() + 1
        mensaje = Mensaje.objects.create(
            conversacion=conversacion,
            rol=rol,
            contenido=contenido,
            orden=siguiente_orden,
        )
        conversacion.save(update_fields=["actualizada_en"])
        return mensaje


@dataclass
class ResultadoOrquestacion:
    """Resultado consolidado producido por el orquestador."""

    conversacion: Conversacion
    respuesta: str
    contexto: dict[str, Any]


class OrquestadorChat:
    """Coordina los tres agentes especializados."""

    def __init__(
        self,
        agente_modelo: AgenteModelo | None = None,
        agente_vista: AgenteVista | None = None,
        agente_controlador: AgenteControlador | None = None,
        agente_rag: AgenteRAG | None = None,
        agente_enrutador: AgenteEnrutadorTematico | None = None,
    ) -> None:
        self.agente_modelo = agente_modelo or AgenteModelo()
        self.agente_vista = agente_vista or AgenteVista()
        self.agente_controlador = agente_controlador or AgenteControlador()
        self.agente_rag = agente_rag or AgenteRAG()
        self.agente_enrutador = agente_enrutador or AgenteEnrutadorTematico()

    def obtener_contexto_inicial(self, identificador_sesion: str) -> dict[str, Any]:
        conversacion = self.agente_controlador.obtener_o_crear_conversacion(identificador_sesion)
        return self.agente_vista.construir_contexto(conversacion)

    def procesar_mensaje(self, identificador_sesion: str, contenido_usuario: str) -> ResultadoOrquestacion:
        """Procesa el mensaje con ORM síncrono y LLM paralelo mediante asyncio."""
        conversacion = self.agente_controlador.obtener_o_crear_conversacion(identificador_sesion)
        self.agente_controlador.registrar_mensaje_usuario(conversacion, contenido_usuario)
        historial = self.agente_controlador.construir_historial_modelo(conversacion)

        contexto_rag = self.agente_rag.buscar(contenido_usuario, max_resultados=4)
        agentes_activados = self.agente_enrutador.seleccionar_agentes(
            mensaje=contenido_usuario,
            contexto_rag=contexto_rag,
        )

        respuestas_agentes = asyncio.run(
            self._generar_respuestas_async(
                historial=historial,
                contexto_rag=contexto_rag,
                agentes_activados=agentes_activados,
            )
        )
        respuestas = []
        for agente, respuesta_agente in zip(agentes_activados, respuestas_agentes):
            etiqueta = agente.capitalize()
            respuestas.append(f"[{etiqueta}] {respuesta_agente}")

        respuesta = "\n\n".join(respuestas)
        self.agente_controlador.registrar_mensaje_asistente(conversacion, respuesta)
        conversacion.refresh_from_db()
        contexto = self.agente_vista.construir_contexto(
            conversacion,
            agentes_activados=agentes_activados,
            fuentes_rag=[fragmento.fuente for fragmento in contexto_rag],
        )
        return ResultadoOrquestacion(
            conversacion=conversacion,
            respuesta=respuesta,
            contexto=contexto,
        )

    async def _generar_respuestas_async(
        self,
        historial: list[dict[str, str]],
        contexto_rag: list[FragmentoRAG],
        agentes_activados: list[str],
    ) -> list[str]:
        tareas = []
        for agente in agentes_activados:
            instrucciones = self.agente_enrutador.instrucciones_para(agente)
            tareas.append(
                self.agente_modelo.generar_respuesta_async(
                    historial=historial,
                    instrucciones_agente=instrucciones,
                    contexto_rag=contexto_rag,
                )
            )
        return await asyncio.gather(*tareas)