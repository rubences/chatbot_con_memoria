"""
Script de publicación del proyecto en Hugging Face Hub.

Uso:
    python publicar_en_hf.py

El script:
  1. Autentica con el token HF_API_KEY definido en .env.
  2. Crea el repositorio en Hugging Face si aún no existe.
  3. Sube todos los archivos del proyecto, excluyendo secretos y artefactos locales.
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi, login, upload_folder

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

REPO_ID = "rubences/memory-assistant-v1"
REPO_TYPE = "model"

# Archivos y carpetas que NUNCA deben subirse al repositorio
IGNORAR = [
    # Secretos y credenciales
    ".env",
    # Artefactos de Python y entornos virtuales
    ".venv",
    "venv",
    "__pycache__",
    "*.py[cod]",
    "*.pyo",
    ".pytest_cache",
    # Base de datos local
    "db.sqlite3",
    # Control de versiones
    ".git",
    # Archivos de sistema
    ".DS_Store",
    "Thumbs.db",
    # Migraciones compiladas (se regeneran con migrate)
    "*/migrations/__pycache__",
]


def main() -> None:
    token = os.getenv("HF_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    if not token or token.startswith("tu_clave"):
        logger.error(
            "No se encontró un token válido. "
            "Define HF_API_KEY en tu archivo .env antes de publicar."
        )
        sys.exit(1)

    logger.info("Autenticando con Hugging Face...")
    login(token=token)

    api = HfApi()
    logger.info("Verificando que el repositorio '%s' exista...", REPO_ID)
    api.create_repo(
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        exist_ok=True,
        private=False,
    )
    logger.info("Repositorio listo.")

    carpeta_proyecto = str(Path(__file__).parent)
    logger.info("Subiendo archivos desde: %s", carpeta_proyecto)

    url = upload_folder(
        folder_path=carpeta_proyecto,
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        ignore_patterns=IGNORAR,
        commit_message="Publicación automática del proyecto memory-assistant-v1",
    )

    logger.info("Publicado con éxito: %s", url)


if __name__ == "__main__":
    main()
