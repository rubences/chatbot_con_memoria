"""Agentes especializados y orquestador del chatbot."""

from __future__ import annotations

import logging
from dataclasses import dataclass
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

    def generar_respuesta(self, historial: list[dict[str, str]]) -> str:
        """Genera la respuesta del asistente a partir del historial completo."""
        try:
            respuesta = self._cliente.chat.completions.create(
                model=self.modelo,
                messages=historial,
            )
        except OpenAIError as error:
            logger.error("Fallo al invocar el modelo: %s", error)
            raise

        contenido = respuesta.choices[0].message.content or ""
        return contenido.strip()


class AgenteVista:
    """Transforma el dominio persistido en contexto consumible por Django."""

    def construir_contexto(self, conversacion: Conversacion) -> dict[str, Any]:
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
        }


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
    ) -> None:
        self.agente_modelo = agente_modelo or AgenteModelo()
        self.agente_vista = agente_vista or AgenteVista()
        self.agente_controlador = agente_controlador or AgenteControlador()

    def obtener_contexto_inicial(self, identificador_sesion: str) -> dict[str, Any]:
        conversacion = self.agente_controlador.obtener_o_crear_conversacion(identificador_sesion)
        return self.agente_vista.construir_contexto(conversacion)

    def procesar_mensaje(self, identificador_sesion: str, contenido_usuario: str) -> ResultadoOrquestacion:
        conversacion = self.agente_controlador.obtener_o_crear_conversacion(identificador_sesion)
        self.agente_controlador.registrar_mensaje_usuario(conversacion, contenido_usuario)
        historial = self.agente_controlador.construir_historial_modelo(conversacion)
        respuesta = self.agente_modelo.generar_respuesta(historial)
        self.agente_controlador.registrar_mensaje_asistente(conversacion, respuesta)
        conversacion.refresh_from_db()
        contexto = self.agente_vista.construir_contexto(conversacion)
        return ResultadoOrquestacion(
            conversacion=conversacion,
            respuesta=respuesta,
            contexto=contexto,
        )