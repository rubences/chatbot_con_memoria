"""
Módulo de gestión del historial de conversación (memoria del chatbot).

Los modelos de lenguaje son stateless; este módulo implementa el patrón
de memoria acumulativa por sesión enviando todo el historial en cada turno.
"""

import logging
from typing import TypedDict

logger = logging.getLogger(__name__)

# Tipo que representa un mensaje individual del historial
Mensaje = TypedDict("Mensaje", {"role": str, "content": str})


class GestorMemoria:
    """Gestiona el historial de conversación de forma acumulativa."""

    def __init__(self, mensaje_sistema: str, limite_mensajes: int = 20) -> None:
        """
        Inicializa la memoria con el mensaje de sistema.

        Args:
            mensaje_sistema: Instrucción de comportamiento para el modelo.
            limite_mensajes: Número máximo de mensajes de usuario/asistente
                             a mantener (sin contar el de sistema).
        """
        self._limite = limite_mensajes
        self._historial: list[Mensaje] = [
            {"role": "system", "content": mensaje_sistema}
        ]
        logger.debug("Memoria inicializada con mensaje de sistema.")

    @property
    def historial(self) -> list[Mensaje]:
        """Devuelve una copia del historial para evitar modificaciones externas."""
        return list(self._historial)

    def agregar_mensaje(self, rol: str, contenido: str) -> None:
        """
        Agrega un mensaje al historial y aplica truncamiento si es necesario.

        Args:
            rol: 'user' o 'assistant'.
            contenido: Texto del mensaje.
        """
        self._historial.append({"role": rol, "content": contenido})
        self._truncar()
        logger.debug("Mensaje de '%s' agregado al historial.", rol)

    def _truncar(self) -> None:
        """
        Elimina los mensajes más antiguos (excepto el de sistema) si se supera
        el límite establecido, preservando siempre el contexto más reciente.
        """
        mensajes_conversacion = self._historial[1:]  # excluye el mensaje de sistema
        if len(mensajes_conversacion) > self._limite:
            exceso = len(mensajes_conversacion) - self._limite
            del self._historial[1 : 1 + exceso]
            logger.debug("Historial truncado: se eliminaron %d mensajes.", exceso)

    def reiniciar(self) -> None:
        """Borra el historial manteniendo únicamente el mensaje de sistema."""
        sistema = self._historial[0]
        self._historial = [sistema]
        logger.debug("Historial reiniciado.")

    def total_mensajes(self) -> int:
        """Devuelve el número de mensajes en el historial (incluyendo el de sistema)."""
        return len(self._historial)
