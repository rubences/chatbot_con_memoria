"""Servicio para parsear documentos con LlamaCloud y alimentar el RAG local."""

from __future__ import annotations

import asyncio
from pathlib import Path

from llama_cloud import AsyncLlamaCloud

from src.config import (
    obtener_llama_cloud_api_key,
    obtener_llama_cloud_tier,
    obtener_llama_cloud_version,
)


class ErrorLlamaCloud(ValueError):
    """Error de configuración o ejecución con LlamaCloud."""


class ServicioLlamaCloudRAG:
    """Conector de LlamaCloud para transformar documentos en contexto RAG."""

    def __init__(self, api_key: str, tier: str = "agentic", version: str = "latest") -> None:
        if not api_key:
            raise ErrorLlamaCloud(
                "LLAMA_CLOUD_API_KEY no está configurada. Añádela en el archivo .env."
            )

        self._cliente = AsyncLlamaCloud(api_key=api_key)
        self._tier = tier
        self._version = version

    async def parsear_documento(self, ruta_archivo: Path) -> tuple[str, str]:
        """Parsea un documento y devuelve (markdown_full, text_full)."""
        if not ruta_archivo.exists() or not ruta_archivo.is_file():
            raise ErrorLlamaCloud(f"No existe el archivo: {ruta_archivo}")

        archivo_subido = await self._cliente.files.create(
            file=str(ruta_archivo),
            purpose="parse",
        )

        resultado = await self._cliente.parsing.parse(
            file_id=archivo_subido.id,
            tier=self._tier,
            version=self._version,
            expand=["markdown_full", "text_full"],
        )

        markdown = (getattr(resultado, "markdown_full", "") or "").strip()
        texto = (getattr(resultado, "text_full", "") or "").strip()
        return markdown, texto

    async def parsear_y_guardar(self, ruta_archivo: Path, carpeta_salida: Path) -> Path:
        """
        Parsea el documento y guarda un archivo markdown para consumo del RAG local.

        Devuelve la ruta del archivo generado.
        """
        markdown, texto = await self.parsear_documento(ruta_archivo)

        if not markdown and not texto:
            raise ErrorLlamaCloud(
                "LlamaCloud no devolvió contenido parseado para el archivo indicado."
            )

        carpeta_salida.mkdir(parents=True, exist_ok=True)
        ruta_destino = carpeta_salida / f"{ruta_archivo.stem}.md"

        contenido = "\n\n".join(
            [
                f"# Documento: {ruta_archivo.name}",
                "## Fuente",
                "Parseado con LlamaCloud y almacenado para recuperación RAG.",
                "## Markdown",
                markdown if markdown else "(vacío)",
                "## Texto Plano",
                texto if texto else "(vacío)",
            ]
        )
        ruta_destino.write_text(contenido, encoding="utf-8")
        return ruta_destino


async def ingestar_documento_llamaindex(
    ruta_archivo: Path,
    carpeta_salida: Path,
) -> Path:
    """Función de alto nivel para ingestar un documento en el repositorio RAG."""
    api_key = obtener_llama_cloud_api_key()
    tier = obtener_llama_cloud_tier()
    version = obtener_llama_cloud_version()

    servicio = ServicioLlamaCloudRAG(api_key=api_key, tier=tier, version=version)
    return await servicio.parsear_y_guardar(ruta_archivo, carpeta_salida)


def ingestar_documento_llamaindex_sync(ruta_archivo: Path, carpeta_salida: Path) -> Path:
    """Wrapper síncrono para comandos Django o scripts."""
    return asyncio.run(ingestar_documento_llamaindex(ruta_archivo, carpeta_salida))
