"""
Módulo de configuración y carga de variables de entorno.
Las credenciales se obtienen exclusivamente desde el archivo .env.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Cargar variables desde el archivo .env de la raíz del proyecto.
# override=True garantiza que los valores del archivo siempre ganan
# sobre cualquier variable ya definida en el proceso (p. ej. de una sesión anterior).
_RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
_RUTA_ENV = _RAIZ_PROYECTO / ".env"
load_dotenv(dotenv_path=_RUTA_ENV, override=True)

logger = logging.getLogger(__name__)


def obtener_proveedor() -> str:
    """Devuelve el proveedor de inferencia configurado."""
    return os.getenv("PROVEEDOR", "openai").strip().lower()


def obtener_clave_api() -> str:
    """
    Devuelve la clave de API según el proveedor configurado.

    - openai: usa OPENAI_API_KEY
    - huggingface: usa HF_API_KEY (o OPENAI_API_KEY como fallback)
    """
    proveedor = obtener_proveedor()
    if proveedor == "huggingface":
        clave = os.getenv("HF_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    else:
        clave = os.getenv("OPENAI_API_KEY", "")

    if not clave:
        logger.warning(
            "No se encontró una clave API válida para el proveedor '%s'.", proveedor
        )
    return clave


def obtener_url_base() -> str | None:
    """Devuelve la URL base para el proveedor configurado."""
    proveedor = obtener_proveedor()
    if proveedor == "huggingface":
        return os.getenv("OPENAI_BASE_URL", "https://router.huggingface.co/v1")
    return os.getenv("OPENAI_BASE_URL")


def obtener_modelo() -> str:
    """Devuelve el nombre del modelo a utilizar."""
    return os.getenv("MODELO", "gpt-4o")


def obtener_temperatura() -> float:
    """Devuelve la temperatura de muestreo del modelo (0.0–2.0)."""
    try:
        valor = float(os.getenv("TEMPERATURA", "0.7"))
        return max(0.0, min(2.0, valor))
    except ValueError:
        logger.warning("TEMPERATURA no es un número válido; se usa 0.7.")
        return 0.7


def obtener_mensaje_sistema() -> str:
    """Devuelve el mensaje de sistema que define la personalidad del asistente."""
    return os.getenv(
        "MENSAJE_SISTEMA",
        "Eres un asistente experto en Python e IA, con un toque sarcástico pero siempre útil.",
    )


def clave_api_parece_placeholder(clave_api: str) -> bool:
    """Indica si la clave parece un valor de ejemplo no válido."""
    valores_placeholder = {
        "",
        "tu_clave_aqui",
        "tu_clave*aqui",
        "cambia_esta_clave",
        "example",
        "demo",
    }
    return clave_api.strip().lower() in valores_placeholder


def obtener_llama_cloud_api_key() -> str:
    """Devuelve la API key de LlamaCloud para ingestión de documentos."""
    return os.getenv("LLAMA_CLOUD_API_KEY", "").strip()


def obtener_llama_cloud_tier() -> str:
    """Devuelve el tier de parseo para LlamaCloud."""
    return os.getenv("LLAMA_CLOUD_TIER", "agentic").strip() or "agentic"


def obtener_llama_cloud_version() -> str:
    """Devuelve la versión del parser de LlamaCloud."""
    return os.getenv("LLAMA_CLOUD_VERSION", "latest").strip() or "latest"


def obtener_llama_workflow_base_url() -> str:
    """Devuelve la URL base del deployment de LlamaIndex Workflows."""
    return os.getenv("LLAMA_WORKFLOW_BASE_URL", "").strip()


def obtener_llama_workflow_nombre() -> str:
    """Devuelve el nombre del workflow remoto a ejecutar."""
    return os.getenv("LLAMA_WORKFLOW_NAME", "").strip()


def obtener_llama_workflow_evento_mensaje() -> str:
    """Devuelve la clave del start_event usada para el mensaje."""
    return os.getenv("LLAMA_WORKFLOW_EVENTO_MENSAJE", "mensaje").strip() or "mensaje"


def obtener_llama_workflow_evento_archivo() -> str:
    """Devuelve la clave del start_event usada para el file_id."""
    return os.getenv("LLAMA_WORKFLOW_EVENTO_ARCHIVO", "file_id").strip() or "file_id"
