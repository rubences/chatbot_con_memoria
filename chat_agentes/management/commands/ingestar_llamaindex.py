"""Comando Django para ingestar documentos en RAG usando LlamaCloud."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from chat_agentes.servicios.llamaindex_rag import (
    ErrorLlamaCloud,
    ingestar_documento_llamaindex_sync,
)


class Command(BaseCommand):
    help = "Parsea un documento con LlamaCloud y lo incorpora al conocimiento RAG local."

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--archivo",
            required=True,
            help="Ruta del documento de entrada (pdf, docx, etc.).",
        )
        parser.add_argument(
            "--salida",
            default="chat_agentes/conocimiento/llamaindex",
            help="Carpeta destino de los archivos parseados para RAG.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        ruta_archivo = Path(options["archivo"]).resolve()
        carpeta_salida = Path(options["salida"]).resolve()

        if not ruta_archivo.exists():
            raise CommandError(f"No existe el archivo: {ruta_archivo}")

        try:
            ruta_generada = ingestar_documento_llamaindex_sync(
                ruta_archivo=ruta_archivo,
                carpeta_salida=carpeta_salida,
            )
        except ErrorLlamaCloud as error:
            raise CommandError(str(error)) from error

        self.stdout.write(self.style.SUCCESS("Documento ingerido correctamente."))
        self.stdout.write(f"Archivo RAG generado: {ruta_generada}")
