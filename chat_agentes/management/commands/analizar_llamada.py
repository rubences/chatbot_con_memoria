"""
Comando de gestión para analizar una transcripción de llamada de call center
mediante el equipo CrewAI multiagente.

Uso:
    python manage.py analizar_llamada                         # Usa la transcripción de ejemplo
    python manage.py analizar_llamada ruta/transcripcion.txt  # Usa un archivo propio
    python manage.py analizar_llamada --salida informe.md     # Guarda el resultado en disco
"""

from __future__ import annotations

import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from chat_agentes.servicios.analisis_llamadas.equipo import EquipoAnalisisLlamadas

logger = logging.getLogger(__name__)

_RUTA_EJEMPLO = Path(__file__).resolve().parent.parent.parent / "datos" / "transcripcion_ejemplo.txt"


class Command(BaseCommand):
    help = (
        "Analiza una transcripción de llamada de servicio al cliente usando un "
        "equipo multiagente CrewAI (Analizador, Especialista QA y Generador de Informes)."
    )

    def add_arguments(self, parser: object) -> None:  # type: ignore[override]
        parser.add_argument(
            "transcripcion",
            nargs="?",
            type=str,
            help=(
                "Ruta al archivo de texto con la transcripción. "
                "Si se omite, se usa la transcripción de ejemplo incluida."
            ),
        )
        parser.add_argument(
            "--salida",
            "-o",
            type=str,
            default=None,
            help="Ruta al archivo donde guardar el informe generado (opcional).",
        )

    def handle(self, *args: object, **options: object) -> None:
        ruta_str: str | None = options.get("transcripcion")  # type: ignore[assignment]
        ruta_salida: str | None = options.get("salida")  # type: ignore[assignment]

        # ── Cargar transcripción ──────────────────────────────────────────────
        if ruta_str:
            ruta = Path(ruta_str)
            if not ruta.exists():
                raise CommandError(f"El archivo '{ruta}' no existe.")
            try:
                transcripcion = ruta.read_text(encoding="utf-8")
            except OSError as error:
                raise CommandError(f"No se pudo leer '{ruta}': {error}") from error
        else:
            if not _RUTA_EJEMPLO.exists():
                raise CommandError(
                    f"La transcripción de ejemplo no se encontró en '{_RUTA_EJEMPLO}'. "
                    "Proporciona una ruta de archivo."
                )
            transcripcion = _RUTA_EJEMPLO.read_text(encoding="utf-8")
            self.stdout.write(
                self.style.NOTICE(
                    f"Usando transcripción de ejemplo: {_RUTA_EJEMPLO.name}"
                )
            )

        # ── Ejecutar equipo ───────────────────────────────────────────────────
        self.stdout.write(
            self.style.WARNING(
                "Iniciando análisis multiagente CrewAI. Esto puede tardar varios minutos…"
            )
        )

        try:
            equipo = EquipoAnalisisLlamadas()
            informe = equipo.analizar(transcripcion)
        except ValueError as error:
            raise CommandError(str(error)) from error
        except RuntimeError as error:
            raise CommandError(str(error)) from error

        # ── Mostrar o guardar informe ─────────────────────────────────────────
        self.stdout.write("\n" + "─" * 72 + "\n")
        self.stdout.write(informe)
        self.stdout.write("\n" + "─" * 72 + "\n")

        if ruta_salida:
            ruta_out = Path(ruta_salida)
            try:
                ruta_out.write_text(informe, encoding="utf-8")
                self.stdout.write(
                    self.style.SUCCESS(f"Informe guardado en: {ruta_out.resolve()}")
                )
            except OSError as error:
                raise CommandError(f"No se pudo guardar el informe: {error}") from error
        else:
            self.stdout.write(
                self.style.SUCCESS("Análisis completado.")
            )
