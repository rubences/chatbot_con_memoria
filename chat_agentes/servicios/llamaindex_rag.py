"""Servicio para parsear documentos con LlamaCloud y alimentar el RAG local."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

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

    @staticmethod
    def _detectar_temas(ruta_archivo: Path, texto: str) -> list[str]:
        """Detecta temas simples para enriquecer enrutamiento de agentes."""
        base = f"{ruta_archivo.as_posix()}\n{texto[:4000]}".lower()
        temas: list[str] = []

        reglas = {
            "python": ["python", "pydantic", "pytest", "langgraph", "crewai", "langsmith"],
            "django": ["django", "orm", "migracion", "migraciones", "modelo", "vistas"],
            "ia": ["ia", "llm", "rag", "prompt", "transformer", "agentic"],
            "negocio": ["finanzas", "contabilidad", "recursos humanos", "supply chain"],
            "automatizacion": ["make", "bubble", "flutterflow", "adalo", "hubspot", "canva"],
        }

        for tema, claves in reglas.items():
            if any(clave in base for clave in claves):
                temas.append(tema)

        if not temas:
            temas.append("general")
        return temas

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

        temas = self._detectar_temas(ruta_archivo, f"{markdown}\n{texto}")

        cabecera = "\n".join(
            [
                "---",
                f"fuente_pdf: {ruta_archivo.name}",
                f"ruta_origen: {ruta_archivo.as_posix()}",
                f"temas: {', '.join(temas)}",
                "origen: llamacloud",
                "---",
            ]
        )

        contenido = "\n\n".join(
            [
                cabecera,
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


def _extraer_metadatos(ruta_archivo: Path) -> tuple[dict[str, str], str]:
    """Extrae front matter básico y devuelve metadatos + cuerpo limpio."""
    try:
        contenido = ruta_archivo.read_text(encoding="utf-8")
    except OSError:
        return {}, ""

    if not contenido.startswith("---\n"):
        return {}, contenido

    partes = contenido.split("\n---\n", maxsplit=1)
    if len(partes) != 2:
        return {}, contenido

    bloque_meta = partes[0].replace("---\n", "", 1)
    cuerpo = partes[1]
    metadatos: dict[str, str] = {}
    for linea in bloque_meta.splitlines():
        if ":" not in linea:
            continue
        clave, valor = linea.split(":", maxsplit=1)
        metadatos[clave.strip()] = valor.strip()
    return metadatos, cuerpo


def regenerar_indice_rag(carpeta_salida: Path) -> Path:
    """Regenera un índice JSON con metadatos de los documentos del RAG."""
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    extensiones = {".md", ".txt", ".rst", ".py"}
    indice: list[dict[str, Any]] = []

    for archivo in sorted(carpeta_salida.rglob("*")):
        if not archivo.is_file() or archivo.suffix.lower() not in extensiones:
            continue
        if archivo.name == "_indice_rag.json":
            continue

        metadatos, cuerpo = _extraer_metadatos(archivo)
        texto_indizable = cuerpo if cuerpo else archivo.read_text(encoding="utf-8")
        tokens = re.findall(r"[a-zA-Z0-9_áéíóúñÁÉÍÓÚÑ]{3,}", texto_indizable.lower())

        temas_raw = metadatos.get("temas", "")
        temas = [tema.strip() for tema in temas_raw.split(",") if tema.strip()]
        if not temas:
            temas = ["general"]

        indice.append(
            {
                "fuente": archivo.name,
                "ruta": archivo.as_posix(),
                "temas": temas,
                "tokens_unicos": len(set(tokens)),
                "tamano_caracteres": len(texto_indizable),
            }
        )

    ruta_indice = carpeta_salida / "_indice_rag.json"
    ruta_indice.write_text(
        json.dumps({"documentos": indice}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return ruta_indice


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


async def ingestar_lote_documentos_llamaindex(
    carpeta_entrada: Path,
    carpeta_salida: Path,
    max_concurrencia: int = 3,
) -> list[Path]:
    """Ingesta todos los PDFs de forma recursiva con concurrencia limitada."""
    if not carpeta_entrada.exists() or not carpeta_entrada.is_dir():
        raise ErrorLlamaCloud(f"No existe la carpeta de entrada: {carpeta_entrada}")

    api_key = obtener_llama_cloud_api_key()
    tier = obtener_llama_cloud_tier()
    version = obtener_llama_cloud_version()
    servicio = ServicioLlamaCloudRAG(api_key=api_key, tier=tier, version=version)

    pdfs = sorted(carpeta_entrada.rglob("*.pdf"))
    if not pdfs:
        return []

    semaforo = asyncio.Semaphore(max(1, max_concurrencia))

    async def _ingestar(pdf: Path) -> Path:
        async with semaforo:
            return await servicio.parsear_y_guardar(pdf, carpeta_salida)

    tareas = [_ingestar(pdf) for pdf in pdfs]
    resultados = await asyncio.gather(*tareas)
    return list(resultados)


def ingestar_lote_documentos_llamaindex_sync(
    carpeta_entrada: Path,
    carpeta_salida: Path,
    max_concurrencia: int = 3,
) -> list[Path]:
    """Wrapper síncrono para ingesta en lote de PDFs."""
    return asyncio.run(
        ingestar_lote_documentos_llamaindex(
            carpeta_entrada=carpeta_entrada,
            carpeta_salida=carpeta_salida,
            max_concurrencia=max_concurrencia,
        )
    )
