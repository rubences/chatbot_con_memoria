"""
Chatbot con memoria conversacional usando Streamlit y la API de OpenAI.

Flujo:
  1. Se asigna un ID de sesión único y estable al navegador.
  2. El historial se carga desde disco (si existe) o se crea nuevo.
  3. Cada mensaje nuevo se persiste automáticamente en JSON.
  4. El panel lateral permite retomar conversaciones anteriores.
"""

import json
import logging
import sys
import uuid
from pathlib import Path

import streamlit as st
from openai import OpenAI, OpenAIError

# Permite importar los módulos de src/ aunque se ejecute desde la raíz
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    clave_api_parece_placeholder,
    obtener_clave_api,
    obtener_mensaje_sistema,
    obtener_modelo,
    obtener_proveedor,
    obtener_url_base,
)
from memoria import GestorMemoria

# ── Configuración de logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Carpeta de persistencia ───────────────────────────────────────────────────
RAIZ = Path(__file__).parent.parent
DIR_CONVERSACIONES = RAIZ / "conversaciones"
DIR_CONVERSACIONES.mkdir(exist_ok=True)

# ── Cliente de OpenAI ─────────────────────────────────────────────────────────
_url_base = obtener_url_base()
_proveedor = obtener_proveedor()
_clave_api = obtener_clave_api()
cliente = OpenAI(
    api_key=_clave_api,
    **({"base_url": _url_base} if _url_base else {}),
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _ruta_sesion(session_id: str) -> Path:
    return DIR_CONVERSACIONES / f"{session_id}.json"


def _listar_conversaciones() -> list[Path]:
    return sorted(
        DIR_CONVERSACIONES.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def _titulo_conversacion(ruta: Path) -> str:
    """Extrae el primer mensaje del usuario como título legible."""
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for msg in datos.get("historial", []):
            if msg.get("role") == "user":
                texto = msg["content"]
                return texto[:55] + ("…" if len(texto) > 55 else "")
    except (json.JSONDecodeError, OSError):
        pass
    return ruta.stem[:8]


# ── ID de sesión estable (persiste en el navegador durante la sesión) ─────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# ── Panel lateral ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Conversaciones")
    if st.button("➕ Nueva conversación", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        if "gestor_memoria" in st.session_state:
            del st.session_state["gestor_memoria"]
        st.rerun()

    conversaciones = _listar_conversaciones()
    if conversaciones:
        st.divider()
        for archivo in conversaciones:
            etiqueta = _titulo_conversacion(archivo)
            activa = archivo.stem == st.session_state.session_id
            prefijo = "▶ " if activa else ""
            if st.button(
                f"{prefijo}{etiqueta}",
                key=archivo.stem,
                use_container_width=True,
            ):
                st.session_state.session_id = archivo.stem
                if "gestor_memoria" in st.session_state:
                    del st.session_state["gestor_memoria"]
                st.rerun()
    else:
        st.caption("Aún no hay conversaciones guardadas.")


# ── Carga o creación del gestor de memoria ────────────────────────────────────
if "gestor_memoria" not in st.session_state:
    st.session_state.gestor_memoria = GestorMemoria.cargar(
        mensaje_sistema=obtener_mensaje_sistema(),
        ruta_archivo=_ruta_sesion(st.session_state.session_id),
    )

gestor: GestorMemoria = st.session_state.gestor_memoria


# ── Interfaz principal ────────────────────────────────────────────────────────
st.title("🤖 Chatbot con Memoria")
st.caption(f"Proveedor: {_proveedor} · Modelo: {obtener_modelo()}")

if clave_api_parece_placeholder(_clave_api):
    st.error(
        "La clave API parece un placeholder. Configura tu .env con una clave real "
        "(OPENAI_API_KEY o HF_API_KEY) y reinicia la app."
    )

# Mostrar el historial de mensajes (omitiendo el mensaje de sistema)
for mensaje in gestor.historial:
    if mensaje["role"] == "system":
        continue
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# Capturar nuevo mensaje del usuario
if entrada := st.chat_input("¿En qué puedo ayudarte?"):
    if clave_api_parece_placeholder(_clave_api):
        st.stop()

    gestor.agregar_mensaje("user", entrada)
    with st.chat_message("user"):
        st.markdown(entrada)

    # Llamar a la API enviando todo el historial acumulado
    with st.chat_message("assistant"):
        try:
            respuesta = cliente.chat.completions.create(
                model=obtener_modelo(),
                messages=gestor.historial,  # type: ignore[arg-type]
            )
            contenido_respuesta = respuesta.choices[0].message.content or ""
            st.markdown(contenido_respuesta)
            gestor.agregar_mensaje("assistant", contenido_respuesta)
            logger.info(
                "Respuesta recibida. Mensajes en historial: %d", gestor.total_mensajes()
            )
        except OpenAIError as error:
            mensaje_error = f"Error al comunicarse con la API: {error}"
            logger.error(mensaje_error)
            st.error(mensaje_error)

# Botón para limpiar la conversación activa sin borrar las demás
if st.button("🗑️ Limpiar esta conversación"):
    gestor.reiniciar()
    st.rerun()
