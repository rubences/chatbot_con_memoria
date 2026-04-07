"""
Módulo de gestión del historial de conversación (memoria del chatbot).

Los modelos de lenguaje son stateless; este módulo implementa el patrón
de memoria acumulativa por sesión enviando todo el historial en cada turno.
El historial puede persistirse en disco como JSON para sobrevivir reinicios.
"""

import json
import logging
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)

# Tipo que representa un mensaje individual del historial
Mensaje = TypedDict("Mensaje", {"role": str, "content": str})


class GestorMemoria:
    """Gestiona el historial de conversación de forma acumulativa y persistente."""

    def __init__(
        self,
        mensaje_sistema: str,
        limite_mensajes: int = 20,
        ruta_archivo: Path | None = None,
    ) -> None:
        """
        Inicializa la memoria con el mensaje de sistema.

        Args:
            mensaje_sistema: Instrucción de comportamiento para el modelo.
            limite_mensajes: Número máximo de mensajes de usuario/asistente
                             a mantener (sin contar el de sistema).
            ruta_archivo: Ruta al archivo JSON donde persistir el historial.
                          Si es None, la memoria solo existe en RAM.
        """
        self._limite = limite_mensajes
        self._ruta = ruta_archivo
        self._historial: list[Mensaje] = [
            {"role": "system", "content": mensaje_sistema}
        ]
        logger.debug("Memoria inicializada con mensaje de sistema.")

    # ── Persistencia ──────────────────────────────────────────────────────────

    @classmethod
    def cargar(
        cls,
        mensaje_sistema: str,
        ruta_archivo: Path,
        limite_mensajes: int = 20,
    ) -> "GestorMemoria":
        """
        Carga una conversación existente desde disco, o crea una nueva si el
        archivo no existe todavía.

        Args:
            mensaje_sistema: Usado solo si se crea una conversación nueva.
            ruta_archivo: Ruta al archivo JSON de persistencia.
            limite_mensajes: Límite de mensajes a mantener.
        """
        gestor = cls(
            mensaje_sistema=mensaje_sistema,
            limite_mensajes=limite_mensajes,
            ruta_archivo=ruta_archivo,
        )
        if ruta_archivo.exists():
            try:
                datos = json.loads(ruta_archivo.read_text(encoding="utf-8"))
                historial_guardado: list[Mensaje] = datos.get("historial", [])
                if historial_guardado:
                    gestor._historial = historial_guardado
                    logger.debug(
                        "Conversación cargada desde '%s' (%d mensajes).",
                        ruta_archivo,
                        len(gestor._historial),
                    )
            except (json.JSONDecodeError, KeyError, OSError) as error:
                logger.warning("No se pudo cargar '%s': %s. Se inicia nueva conversación.", ruta_archivo, error)
        return gestor

    def guardar(self) -> None:
        """Persiste el historial actual en disco como JSON."""
        if self._ruta is None:
            return
        try:
            self._ruta.parent.mkdir(parents=True, exist_ok=True)
            self._ruta.write_text(
                json.dumps({"historial": self._historial}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            logger.error("Error al guardar la conversación en '%s': %s", self._ruta, error)

    # ── Propiedades y mutación ────────────────────────────────────────────────

    @property
    def historial(self) -> list[Mensaje]:
        """Devuelve una copia del historial para evitar modificaciones externas."""
        return list(self._historial)

    def agregar_mensaje(self, rol: str, contenido: str) -> None:
        """
        Agrega un mensaje al historial, aplica truncamiento y persiste en disco.

        Args:
            rol: 'user' o 'assistant'.
            contenido: Texto del mensaje.
        """
        self._historial.append({"role": rol, "content": contenido})
        self._truncar()
        self.guardar()
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
        self.guardar()
        logger.debug("Historial reiniciado.")

    def total_mensajes(self) -> int:
        """Devuelve el número de mensajes en el historial (incluyendo el de sistema)."""
        return len(self._historial)
