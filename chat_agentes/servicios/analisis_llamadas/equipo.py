"""
Equipo CrewAI para el análisis de transcripciones de llamadas de servicio al cliente.

Implementa tres agentes especializados que colaboran en secuencia:
  1. Analizador de Transcripciones – extrae conocimientos, sentimiento y palabras clave.
  2. Especialista en Control de Calidad – evalúa con métricas de call center (CSAT, CES, NPS…).
  3. Generador de Informes – compila un informe ejecutivo con recomendaciones accionables.
"""

from __future__ import annotations

import logging
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task

from chat_agentes.servicios.analisis_llamadas.herramientas import (
    HerramientaAnalisisSentimiento,
    HerramientaExtraccionPalabrasClave,
)
from src.config import (
    obtener_clave_api,
    obtener_mensaje_sistema,
    obtener_modelo,
    obtener_temperatura,
    obtener_url_base,
)

logger = logging.getLogger(__name__)


def _construir_llm() -> LLM:
    """
    Construye la instancia LLM compatible con crewAI/litellm usando
    la configuración ya existente del proyecto (src/config.py).
    """
    modelo = obtener_modelo()
    clave_api = obtener_clave_api()
    temperatura = obtener_temperatura()
    url_base = obtener_url_base()

    # litellm requiere el prefijo "openai/" para proveedores compatibles sin prefijo
    if not modelo.startswith(("openai/", "huggingface/", "ollama/", "anthropic/")):
        modelo_litellm = f"openai/{modelo}"
    else:
        modelo_litellm = modelo

    kwargs: dict[str, Any] = {
        "model": modelo_litellm,
        "api_key": clave_api,
        "temperature": temperatura,
    }
    if url_base:
        kwargs["base_url"] = url_base

    logger.debug("LLM crewAI inicializado: modelo=%s base_url=%s", modelo_litellm, url_base)
    return LLM(**kwargs)


class EquipoAnalisisLlamadas:
    """
    Orquesta el análisis completo de una transcripción de llamada de servicio
    al cliente mediante tres agentes crewAI especializados.

    Uso::

        equipo = EquipoAnalisisLlamadas()
        informe = equipo.analizar(texto_transcripcion)
    """

    def __init__(self) -> None:
        self._llm = _construir_llm()
        self._herramienta_sentimiento = HerramientaAnalisisSentimiento()
        self._herramienta_palabras_clave = HerramientaExtraccionPalabrasClave()

    # ── Definición de agentes ─────────────────────────────────────────────────

    def _analizador_transcripciones(self) -> Agent:
        return Agent(
            role="Analizador de Transcripciones",
            goal=(
                "Analizar la transcripción proporcionada y extraer conocimientos clave, "
                "temas principales, sentimiento de cada participante y riesgos de escalada."
            ),
            backstory=(
                "Eres el Analizador de Transcripciones, responsable de revisar "
                "transcripciones de llamadas de servicio al cliente. Identificas "
                "información importante y la resumes en un informe detallado que "
                "el Especialista en Control de Calidad utilizará como base. "
                "Tienes acceso a herramientas avanzadas de análisis de texto que "
                "te permiten procesar e interpretar los datos de forma eficaz."
            ),
            tools=[self._herramienta_sentimiento, self._herramienta_palabras_clave],
            llm=self._llm,
            verbose=False,
        )

    def _especialista_calidad(self) -> Agent:
        return Agent(
            role="Especialista en Control de Calidad",
            goal=(
                "Evaluar la calidad de la interacción de servicio al cliente basándose "
                "en el informe del Analizador de Transcripciones y en métricas estándar "
                "de call center (CSAT, CES, NPS, FCR, AHT). "
                "Marcar como alta prioridad cualquier riesgo de escalada."
            ),
            backstory=(
                "Eres el Especialista en Control de Calidad con amplia experiencia "
                "en la evaluación de interacciones de servicio al cliente. Conoces "
                "en profundidad las métricas de evaluación de call center y los "
                "estándares del sector. Evalúas el rendimiento de los agentes, "
                "detectas riesgos de escalada y proporciones retroalimentación "
                "para mejorar la calidad global del servicio."
            ),
            llm=self._llm,
            verbose=False,
        )

    def _generador_informes(self) -> Agent:
        return Agent(
            role="Generador de Informes",
            goal=(
                "Generar un informe completo, organizado y accionable para gestores "
                "de call center, compilando los hallazgos del Analizador de Transcripciones "
                "y del Especialista en Control de Calidad."
            ),
            backstory=(
                "Eres el Generador de Informes, especializado en transformar datos de "
                "análisis y evaluación de calidad en informes estructurados y fáciles "
                "de entender. Tus informes son directos, bien organizados y siempre "
                "incluyen secciones claras con resumen ejecutivo, hallazgos clave y "
                "recomendaciones priorizadas para la mejora continua del servicio."
            ),
            llm=self._llm,
            verbose=False,
        )

    # ── Definición de tareas ──────────────────────────────────────────────────

    def _tarea_analisis(self, agente: Agent, transcripcion: str) -> Task:
        return Task(
            description=(
                f"Realiza un análisis exhaustivo de la siguiente transcripción de llamada "
                f"de servicio al cliente:\n\n{transcripcion}\n\n"
                "Instrucciones:\n"
                "1. Usa la Herramienta de Análisis de Sentimientos para determinar "
                "el sentimiento general del cliente y del agente.\n"
                "2. Usa la Herramienta de Extracción de Palabras Clave para identificar "
                "términos y frases clave.\n"
                "3. Resume los puntos principales de la interacción.\n"
                "4. Identifica cualquier riesgo de escalada (amenaza de reseña negativa, "
                "solicitud de supervisor, abandono de cliente) y márcalos con alta prioridad."
            ),
            expected_output=(
                "Informe de análisis que incluya:\n"
                "- Resumen de la interacción\n"
                "- Sentimiento del cliente y del agente (con el resultado de la herramienta)\n"
                "- Palabras y frases clave extraídas\n"
                "- Temas principales identificados\n"
                "- Riesgos de escalada detectados y clasificados por prioridad"
            ),
            agent=agente,
        )

    def _tarea_calidad(self, agente: Agent) -> Task:
        return Task(
            description=(
                "Revisa el informe del Analizador de Transcripciones y evalúa la calidad "
                "de la interacción usando las siguientes métricas estándar de call center:\n"
                "- CSAT (Customer Satisfaction Score)\n"
                "- CES (Customer Effort Score)\n"
                "- NPS (Net Promoter Score)\n"
                "- FCR (First Call Resolution)\n"
                "- Cumplimiento de protocolos de atención al cliente\n\n"
                "Evalúa con una puntuación numérica o cualitativa cada métrica, "
                "señala riesgos de escalada de alto riesgo y proporciona recomendaciones "
                "concretas y priorizadas para mejorar el rendimiento del agente."
            ),
            expected_output=(
                "Informe de evaluación de calidad que incluya:\n"
                "- Puntuación de cada métrica (CSAT, CES, NPS, FCR, cumplimiento de protocolo)\n"
                "- Identificación de escaladas de alto riesgo\n"
                "- Análisis del comportamiento del agente\n"
                "- Mínimo 5 recomendaciones concretas y priorizadas para mejorar la calidad"
            ),
            agent=agente,
        )

    def _tarea_informe(
        self,
        agente: Agent,
        contexto: list[Task],
    ) -> Task:
        return Task(
            description=(
                "Compila los resultados del Analizador de Transcripciones y del Especialista "
                "en Control de Calidad en un informe ejecutivo completo para gestores de "
                "call center. El informe debe estar en Markdown bien estructurado con las "
                "siguientes secciones:\n"
                "1. **Resumen Ejecutivo** – puntos clave en 3-5 frases.\n"
                "2. **Análisis de la Transcripción** – hallazgos del analizador: sentimiento, "
                "palabras clave, temas y riesgos.\n"
                "3. **Evaluación de Calidad** – métricas, puntuaciones y análisis del agente.\n"
                "4. **Plan de Acción** – recomendaciones priorizadas (inmediatas, a corto plazo "
                "y estratégicas) para gestores de call center.\n\n"
                "Asegúrate de que el informe sea claro, bien redactado y fácil de entender "
                "para alguien que no estuvo presente en la llamada."
            ),
            expected_output=(
                "Informe completo en Markdown con secciones claramente etiquetadas: "
                "Resumen Ejecutivo, Análisis de la Transcripción (con sentimiento, palabras clave "
                "y riesgos de escalada), Evaluación de Calidad (con métricas de call center) "
                "y Plan de Acción con recomendaciones priorizadas para gestores."
            ),
            agent=agente,
            context=contexto,
        )

    # ── Método principal ──────────────────────────────────────────────────────

    def analizar(self, transcripcion: str) -> str:
        """
        Ejecuta el pipeline completo de análisis de transcripción.

        Args:
            transcripcion: Texto completo de la transcripción de la llamada.

        Returns:
            Informe Markdown generado por el agente Generador de Informes.

        Raises:
            ValueError: Si la transcripción está vacía.
            RuntimeError: Si el proceso crewAI falla internamente.
        """
        transcripcion = transcripcion.strip()
        if not transcripcion:
            raise ValueError("La transcripción no puede estar vacía.")

        analizador = self._analizador_transcripciones()
        especialista = self._especialista_calidad()
        generador = self._generador_informes()

        tarea_analisis = self._tarea_analisis(analizador, transcripcion)
        tarea_calidad = self._tarea_calidad(especialista)
        tarea_informe = self._tarea_informe(generador, [tarea_analisis, tarea_calidad])

        equipo = Crew(
            agents=[analizador, especialista, generador],
            tasks=[tarea_analisis, tarea_calidad, tarea_informe],
            process=Process.sequential,
            verbose=False,
        )

        try:
            resultado = equipo.kickoff()
            informe = str(resultado)
            logger.info("Análisis de llamada completado (%d caracteres).", len(informe))
            return informe
        except Exception as error:
            logger.error("Error durante el análisis crewAI: %s", error)
            raise RuntimeError(f"El equipo de análisis falló: {error}") from error
