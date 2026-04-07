"""Comando integral: ingesta en lote + regeneración de índice RAG."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from chat_agentes.servicios.llamaindex_rag import (
    ErrorLlamaCloud,
    ingestar_lote_documentos_llamaindex_sync,
    regenerar_indice_rag,
)


class Command(BaseCommand):
    help = (
        "Ingesta todos los PDFs de una carpeta con LlamaCloud, "
        "genera markdowns con metadatos y regenera el índice RAG."
    )

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--carpeta",
            default="contexto",
            help="Carpeta de entrada donde buscar PDFs de forma recursiva.",
        )
        parser.add_argument(
            "--salida",
            default="chat_agentes/conocimiento/llamaindex",
            help="Carpeta destino para documentos parseados e índice RAG.",
        )
        parser.add_argument(
            "--max-concurrencia",
            type=int,
            default=3,
            help="Número de parseos simultáneos contra LlamaCloud.",
        )
        parser.add_argument(
            "--solo-indice",
            action="store_true",
            help="No ingesta PDFs; solo regenera el índice con archivos ya existentes.",
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        carpeta_entrada = Path(options["carpeta"]).resolve()
        carpeta_salida = Path(options["salida"]).resolve()
        max_concurrencia = options["max_concurrencia"]
        solo_indice = bool(options["solo_indice"])

        if max_concurrencia < 1:
            raise CommandError("--max-concurrencia debe ser mayor o igual a 1.")

        procesados = []
        if not solo_indice:
            if not carpeta_entrada.exists():
                raise CommandError(f"No existe la carpeta de entrada: {carpeta_entrada}")
            try:
                procesados = ingestar_lote_documentos_llamaindex_sync(
                    carpeta_entrada=carpeta_entrada,
                    carpeta_salida=carpeta_salida,
                    max_concurrencia=max_concurrencia,
                )
            except ErrorLlamaCloud as error:
                raise CommandError(str(error)) from error

            self.stdout.write(self.style.SUCCESS(f"Documentos ingeridos: {len(procesados)}"))

        ruta_indice = regenerar_indice_rag(carpeta_salida)
        self.stdout.write(self.style.SUCCESS("Índice RAG regenerado correctamente."))
        self.stdout.write(f"Ruta del índice: {ruta_indice}")

        if procesados:
            for ruta in procesados[:10]:
                self.stdout.write(f"- {ruta}")
            if len(procesados) > 10:
                self.stdout.write(f"... y {len(procesados) - 10} más")
