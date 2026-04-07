"""Cliente para ejecutar agentes desplegados con LlamaIndex Workflows."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from llama_cloud import LlamaCloud
from llama_agents.client import WorkflowClient

from src.config import (
    obtener_llama_cloud_api_key,
    obtener_llama_workflow_base_url,
    obtener_llama_workflow_evento_archivo,
    obtener_llama_workflow_evento_mensaje,
    obtener_llama_workflow_nombre,
)


class ErrorWorkflowLlamaIndex(ValueError):
    """Error de configuración o ejecución del workflow remoto."""


class ServicioWorkflowLlamaIndex:
    """Encapsula la interacción con un deployment remoto de LlamaIndex Workflows."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        workflow_name: str,
        evento_mensaje: str,
        evento_archivo: str,
    ) -> None:
        if not api_key:
            raise ErrorWorkflowLlamaIndex(
                "LLAMA_CLOUD_API_KEY no está configurada. Añádela en el archivo .env."
            )
        if not base_url:
            raise ErrorWorkflowLlamaIndex(
                "LLAMA_WORKFLOW_BASE_URL no está configurada. Añádela en el archivo .env."
            )
        if not workflow_name:
            raise ErrorWorkflowLlamaIndex(
                "LLAMA_WORKFLOW_NAME no está configurada. Añádela en el archivo .env."
            )

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.workflow_name = workflow_name
        self.evento_mensaje = evento_mensaje
        self.evento_archivo = evento_archivo
        self._llama_cloud = LlamaCloud(api_key=api_key)

    async def ejecutar(
        self,
        mensaje: str | None = None,
        ruta_archivo: Path | None = None,
        start_event_extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ejecuta el workflow remoto y devuelve resultado + stream de eventos."""
        start_event: dict[str, Any] = dict(start_event_extra or {})

        if mensaje:
            start_event[self.evento_mensaje] = mensaje

        if ruta_archivo is not None:
            if not ruta_archivo.exists() or not ruta_archivo.is_file():
                raise ErrorWorkflowLlamaIndex(f"No existe el archivo: {ruta_archivo}")
            with ruta_archivo.open("rb") as descriptor:
                archivo = self._llama_cloud.files.create(file=descriptor, purpose="user_data")
            start_event[self.evento_archivo] = archivo.id

        base_url_segura = self._normalizar_base_url(self.base_url)
        async with httpx.AsyncClient(
            base_url=base_url_segura,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0,
        ) as httpx_client:
            client = WorkflowClient(httpx_client=httpx_client)
            workflows = await client.list_workflows()
            handler = await client.run_workflow_nowait(
                self.workflow_name,
                start_event=start_event,
            )

            eventos = []
            async for evento in client.get_workflow_events(handler.handler_id):
                eventos.append(
                    {
                        "type": getattr(evento, "type", "unknown"),
                        "value": getattr(evento, "value", None),
                    }
                )

            resultado = await client.get_handler(handler.handler_id)
            return {
                "handler_id": handler.handler_id,
                "workflows": workflows,
                "eventos": eventos,
                "resultado": getattr(resultado, "result", None),
                "start_event": start_event,
            }

    @staticmethod
    def _normalizar_base_url(base_url: str) -> str:
        """Codifica espacios y caracteres no ASCII en el segmento final si hace falta."""
        if "/deployments/" not in base_url:
            return base_url
        prefijo, sufijo = base_url.rsplit("/deployments/", maxsplit=1)
        return f"{prefijo}/deployments/{quote(sufijo, safe='-_')}"


async def ejecutar_workflow_llamaindex(
    mensaje: str | None = None,
    ruta_archivo: Path | None = None,
    start_event_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construye el servicio desde .env y ejecuta el workflow remoto."""
    servicio = ServicioWorkflowLlamaIndex(
        api_key=obtener_llama_cloud_api_key(),
        base_url=obtener_llama_workflow_base_url(),
        workflow_name=obtener_llama_workflow_nombre(),
        evento_mensaje=obtener_llama_workflow_evento_mensaje(),
        evento_archivo=obtener_llama_workflow_evento_archivo(),
    )
    return await servicio.ejecutar(
        mensaje=mensaje,
        ruta_archivo=ruta_archivo,
        start_event_extra=start_event_extra,
    )


def ejecutar_workflow_llamaindex_sync(
    mensaje: str | None = None,
    ruta_archivo: Path | None = None,
    start_event_extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrapper síncrono para management commands y scripts."""
    return asyncio.run(
        ejecutar_workflow_llamaindex(
            mensaje=mensaje,
            ruta_archivo=ruta_archivo,
            start_event_extra=start_event_extra,
        )
    )


def parsear_evento_extra(valor: str | None) -> dict[str, Any]:
    """Parsea un JSON opcional para enriquecer el start_event."""
    if not valor:
        return {}
    try:
        datos = json.loads(valor)
    except json.JSONDecodeError as error:
        raise ErrorWorkflowLlamaIndex("El valor de --evento-json no es JSON válido.") from error
    if not isinstance(datos, dict):
        raise ErrorWorkflowLlamaIndex("El valor de --evento-json debe ser un objeto JSON.")
    return datos
