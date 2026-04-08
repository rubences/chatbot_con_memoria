"""Orquestador ACP para interoperar con estrategias CrewAI y ReWOO.

Entrada: mensaje ACP JSON con contenido y metadatos.
Salida: mensaje ACP JSON con informe y trazabilidad.
"""

from __future__ import annotations

from dataclasses import dataclass

from chat_agentes.agentes import ErrorConfiguracionModelo
from chat_agentes.servicios.acp import ACPMensaje, construir_mensaje
from chat_agentes.servicios.analisis_llamadas.equipo import EquipoAnalisisLlamadas
from chat_agentes.servicios.analisis_llamadas.rewoo import OrquestadorReWOOAnalisis


@dataclass
class ResultadoACP:
    """Resultado de una corrida ACP."""

    entrada: ACPMensaje
    salida: ACPMensaje


class OrquestadorACPAnalisis:
    """Coordina analisis de llamadas usando mensajes ACP estandarizados."""

    def ejecutar(self, mensaje_entrada: ACPMensaje) -> ResultadoACP:
        """Ejecuta el flujo segun metadata ACP y devuelve mensaje de salida."""
        if not mensaje_entrada.parts:
            raise ValueError("El mensaje ACP debe incluir al menos una parte.")

        transcripcion = (mensaje_entrada.parts[0].content or "").strip()
        if not transcripcion:
            raise ValueError("La parte principal del mensaje ACP está vacía.")

        metadata = mensaje_entrada.metadata or {}
        estrategia = str(metadata.get("estrategia", "crewai")).lower().strip()
        usar_busqueda_web = bool(metadata.get("usar_busqueda_web", False))

        if estrategia not in {"crewai", "rewoo"}:
            raise ValueError("metadata.estrategia debe ser 'crewai' o 'rewoo'.")

        if estrategia == "rewoo":
            orquestador = OrquestadorReWOOAnalisis(usar_busqueda_web=usar_busqueda_web)
            informe = orquestador.analizar(transcripcion).informe_markdown
        else:
            informe = EquipoAnalisisLlamadas().analizar(transcripcion)

        mensaje_salida = construir_mensaje(
            role="assistant",
            contenido=informe,
            metadata={
                "protocolo": "ACP",
                "estrategia": estrategia,
                "usar_busqueda_web": usar_busqueda_web,
                "estado": "completed",
            },
        )

        return ResultadoACP(entrada=mensaje_entrada, salida=mensaje_salida)


def parsear_mensaje_acp(payload: dict[str, object]) -> ACPMensaje:
    """Convierte un payload JSON en un objeto ACPMensaje."""
    role = str(payload.get("role", "user"))
    metadata_raw = payload.get("metadata", {})
    parts_raw = payload.get("parts", [])

    if not isinstance(parts_raw, list):
        raise ValueError("'parts' debe ser una lista.")
    if not isinstance(metadata_raw, dict):
        raise ValueError("'metadata' debe ser un objeto JSON.")

    from chat_agentes.servicios.acp import ACPParteMensaje

    partes: list[ACPParteMensaje] = []
    for parte in parts_raw:
        if not isinstance(parte, dict):
            raise ValueError("Cada item en 'parts' debe ser un objeto.")
        contenido = str(parte.get("content", "")).strip()
        if not contenido:
            continue
        partes.append(
            ACPParteMensaje(
                content=contenido,
                content_type=str(parte.get("content_type", "text/plain")),
            )
        )

    if not partes:
        raise ValueError("No se encontró contenido válido en 'parts'.")

    metadata_limpia: dict[str, str | int | float | bool] = {}
    for clave, valor in metadata_raw.items():
        if isinstance(valor, (str, int, float, bool)):
            metadata_limpia[str(clave)] = valor

    return ACPMensaje(role=role, parts=partes, metadata=metadata_limpia)
