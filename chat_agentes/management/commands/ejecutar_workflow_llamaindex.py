"""Comando Django para invocar un agente remoto desplegado con LlamaIndex Workflows."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from chat_agentes.servicios.llamaindex_workflow import (
    ErrorWorkflowLlamaIndex,
    ejecutar_workflow_llamaindex_sync,
    parsear_evento_extra,
)


class Command(BaseCommand):
    help = "Ejecuta un workflow remoto de LlamaIndex usando la configuración del archivo .env."

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--mensaje",
            default="",
            help="Mensaje a enviar al workflow remoto.",
        )
        parser.add_argument(
            "--archivo",
            help="Ruta opcional de archivo a subir antes de invocar el workflow.",
        )
        parser.add_argument(
            "--evento-json",
            help="JSON opcional para fusionar en start_event.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        ruta_archivo = None
        if options.get("archivo"):
            ruta_archivo = Path(options["archivo"]).resolve()

        try:
            resultado = ejecutar_workflow_llamaindex_sync(
                mensaje=str(options.get("mensaje", "")).strip() or None,
                ruta_archivo=ruta_archivo,
                start_event_extra=parsear_evento_extra(options.get("evento_json")),
            )
        except ErrorWorkflowLlamaIndex as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS("Workflow ejecutado correctamente."))
        self.stdout.write(f"Handler ID: {resultado['handler_id']}")
        self.stdout.write("Start event enviado:")
        self.stdout.write(json.dumps(resultado["start_event"], ensure_ascii=False, indent=2))
        self.stdout.write("Resultado final:")
        self.stdout.write(json.dumps(resultado["resultado"], ensure_ascii=False, indent=2, default=str))
        self.stdout.write("Eventos recibidos:")
        self.stdout.write(json.dumps(resultado["eventos"], ensure_ascii=False, indent=2, default=str))
