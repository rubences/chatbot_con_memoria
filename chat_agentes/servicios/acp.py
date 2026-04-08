"""Capa ACP simplificada para interoperabilidad entre agentes.

Define un formato de mensajeria JSON estandarizado e independiente del marco,
con metadatos para controlar estrategia, herramientas y trazabilidad.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


@dataclass
class ACPParteMensaje:
    """Parte individual de un mensaje ACP."""

    content: str
    content_type: str = "text/plain"


@dataclass
class ACPMensaje:
    """Mensaje ACP con metadatos de interoperabilidad."""

    role: str
    parts: list[ACPParteMensaje]
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds")
    )

    def a_dict(self) -> dict[str, object]:
        """Serializa el mensaje a diccionario JSON-friendly."""
        return asdict(self)


def construir_mensaje(
    role: str,
    contenido: str,
    metadata: dict[str, str | int | float | bool] | None = None,
) -> ACPMensaje:
    """Crea un mensaje ACP de una sola parte de texto."""
    return ACPMensaje(
        role=role,
        parts=[ACPParteMensaje(content=contenido)],
        metadata=metadata or {},
    )
