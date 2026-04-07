"""
Chatbot con memoria conversacional usando Streamlit y la API de OpenAI.

Flujo:
  1. El usuario escribe un mensaje.
  2. Se añade al historial (memoria acumulativa).
  3. Se envía TODO el historial a la API para que el modelo tenga contexto.
  4. La respuesta se muestra y se guarda en el historial.
"""

import logging
import sys
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

# ── Cliente de OpenAI ─────────────────────────────────────────────────────────
_url_base = obtener_url_base()
_proveedor = obtener_proveedor()
_clave_api = obtener_clave_api()
cliente = OpenAI(
    api_key=_clave_api,
    **({"base_url": _url_base} if _url_base else {}),
)

# ── Interfaz Streamlit ────────────────────────────────────────────────────────
st.title("🤖 Chatbot con Memoria")
st.caption("Mantiene el contexto de toda la conversación en cada turno.")
st.caption(f"Proveedor activo: {_proveedor}")

if clave_api_parece_placeholder(_clave_api):
    st.error(
        "La clave API parece un placeholder. Configura tu .env con una clave real "
        "(OPENAI_API_KEY o HF_API_KEY) y reinicia la app."
    )

# Inicializar la memoria en la sesión de Streamlit (persiste entre reruns)
if "gestor_memoria" not in st.session_state:
    st.session_state.gestor_memoria = GestorMemoria(
        mensaje_sistema=obtener_mensaje_sistema()
    )

gestor: GestorMemoria = st.session_state.gestor_memoria

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
            logger.info("Respuesta recibida. Mensajes en historial: %d", gestor.total_mensajes())
        except OpenAIError as error:
            mensaje_error = f"Error al comunicarse con la API: {error}"
            logger.error(mensaje_error)
            st.error(mensaje_error)

# Botón para reiniciar la conversación
if st.button("🗑️ Nueva conversación"):
    gestor.reiniciar()
    st.rerun()
