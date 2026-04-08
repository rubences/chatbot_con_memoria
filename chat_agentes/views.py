"""Vistas Django para la interfaz del chatbot multiagente."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from chat_agentes.agentes import ErrorConfiguracionModelo, OrquestadorChat
from chat_agentes.models import Conversacion
from chat_agentes.servicios.acp_orquestador import OrquestadorACPAnalisis, parsear_mensaje_acp

logger = logging.getLogger(__name__)

_RUTA_TRANSCRIPCION_EJEMPLO = (
    Path(__file__).parent / "datos" / "transcripcion_ejemplo.txt"
)


def _obtener_identificador_sesion(request: HttpRequest) -> str:
	if request.session.session_key is None:
		request.session.create()
	return str(request.session.session_key)


@require_GET
def inicio(request: HttpRequest) -> HttpResponse:
	identificador_sesion = _obtener_identificador_sesion(request)
	contexto = {
		"error_configuracion": None,
		"estado": "listo",
	}

	try:
		orquestador = OrquestadorChat()
		contexto.update(orquestador.obtener_contexto_inicial(identificador_sesion))
	except ErrorConfiguracionModelo as error:
		contexto.update(
			{
				"mensajes": [],
				"titulo": "Configuración pendiente",
				"proveedor": "sin configurar",
				"modelo": "sin configurar",
				"error_configuracion": str(error),
				"estado": "error",
			}
		)

	return render(request, "chat_agentes/inicio.html", contexto)


@require_GET
def docs_multiagente(request: HttpRequest) -> HttpResponse:
	"""Muestra documentación web sobre estrategias y marcos multiagente."""
	return render(request, "chat_agentes/docs_multiagente.html")


@require_POST
def enviar_mensaje(request: HttpRequest) -> JsonResponse:
	identificador_sesion = _obtener_identificador_sesion(request)

	if request.content_type == "application/json":
		cuerpo = json.loads(request.body.decode("utf-8"))
		contenido_usuario = str(cuerpo.get("mensaje", "")).strip()
	else:
		contenido_usuario = request.POST.get("mensaje", "").strip()

	if not contenido_usuario:
		return JsonResponse({"error": "Debes escribir un mensaje."}, status=400)

	try:
		resultado = OrquestadorChat().procesar_mensaje(identificador_sesion, contenido_usuario)
	except ErrorConfiguracionModelo as error:
		return JsonResponse({"error": str(error)}, status=400)

	return JsonResponse(
		{
			"respuesta": resultado.respuesta,
			"contexto": resultado.contexto,
		}
	)


@require_POST
def limpiar_conversacion(request: HttpRequest) -> JsonResponse:
	"""Elimina la conversación de la sesión actual y crea una nueva en blanco."""
	identificador_sesion = _obtener_identificador_sesion(request)
	Conversacion.objects.filter(identificador_sesion=identificador_sesion).delete()
	orquestador = OrquestadorChat()
	orquestador.agente_controlador.obtener_o_crear_conversacion(identificador_sesion)
	return JsonResponse({"ok": True})


# ── Análisis de llamadas (CrewAI) ─────────────────────────────────────────────

def analisis_llamada(request: HttpRequest) -> HttpResponse | JsonResponse:
	"""
	GET  – Muestra el formulario de análisis con la transcripción de ejemplo.
	POST – Ejecuta el equipo CrewAI y devuelve el informe en JSON.
	"""
	if request.method == "GET":
		transcripcion_ejemplo = ""
		if _RUTA_TRANSCRIPCION_EJEMPLO.exists():
			try:
				transcripcion_ejemplo = _RUTA_TRANSCRIPCION_EJEMPLO.read_text(encoding="utf-8")
			except OSError:
				pass
		return render(
			request,
			"chat_agentes/analisis_llamadas.html",
			{
				"transcripcion_ejemplo": transcripcion_ejemplo,
				"estrategia_default": "crewai",
			},
		)

	# POST ────────────────────────────────────────────────────────────────────
	if request.content_type == "application/json":
		cuerpo = json.loads(request.body.decode("utf-8"))
		transcripcion = str(cuerpo.get("transcripcion", "")).strip()
		estrategia = str(cuerpo.get("estrategia", "crewai")).strip().lower()
		usar_busqueda_web = bool(cuerpo.get("usar_busqueda_web", False))
	else:
		transcripcion = request.POST.get("transcripcion", "").strip()
		estrategia = request.POST.get("estrategia", "crewai").strip().lower()
		usar_busqueda_web = request.POST.get("usar_busqueda_web", "false").lower() == "true"

	if not transcripcion:
		return JsonResponse({"error": "Debes proporcionar el texto de la transcripción."}, status=400)
	if estrategia not in {"crewai", "rewoo"}:
		return JsonResponse({"error": "La estrategia debe ser 'crewai' o 'rewoo'."}, status=400)

	try:
		if estrategia == "rewoo":
			from chat_agentes.servicios.analisis_llamadas.rewoo import OrquestadorReWOOAnalisis
			orquestador = OrquestadorReWOOAnalisis(usar_busqueda_web=usar_busqueda_web)
			resultado = orquestador.analizar(transcripcion)
			informe = resultado.informe_markdown
		else:
			from chat_agentes.servicios.analisis_llamadas.equipo import EquipoAnalisisLlamadas
			equipo = EquipoAnalisisLlamadas()
			informe = equipo.analizar(transcripcion)
	except ValueError as error:
		return JsonResponse({"error": str(error)}, status=400)
	except ErrorConfiguracionModelo as error:
		return JsonResponse({"error": str(error)}, status=400)
	except RuntimeError as error:
		logger.error("Fallo en el análisis CrewAI/ReWOO: %s", error)
		mensaje = str(error)
		if "429" in mensaje or "rate" in mensaje.lower():
			return JsonResponse({"error": mensaje}, status=429)
		return JsonResponse({"error": mensaje}, status=500)

	return JsonResponse(
		{
			"informe": informe,
			"estrategia": estrategia,
			"usar_busqueda_web": usar_busqueda_web,
		}
	)


@require_POST
def acp_run(request: HttpRequest) -> JsonResponse:
	"""Ejecuta un flujo de analisis usando un mensaje ACP estandarizado."""
	if request.content_type != "application/json":
		return JsonResponse({"error": "El endpoint ACP requiere application/json."}, status=400)

	try:
		payload = json.loads(request.body.decode("utf-8"))
		if not isinstance(payload, dict):
			return JsonResponse({"error": "El payload ACP debe ser un objeto JSON."}, status=400)

		mensaje_payload = payload.get("message")
		if not isinstance(mensaje_payload, dict):
			return JsonResponse(
				{"error": "Falta el objeto 'message' con formato ACP."},
				status=400,
			)

		mensaje = parsear_mensaje_acp(mensaje_payload)
		resultado = OrquestadorACPAnalisis().ejecutar(mensaje)
		return JsonResponse(
			{
				"protocol": "ACP",
				"run_status": "completed",
				"input_message": resultado.entrada.a_dict(),
				"output_message": resultado.salida.a_dict(),
			}
		)
	except (ValueError, ErrorConfiguracionModelo) as error:
		return JsonResponse({"error": str(error)}, status=400)
	except RuntimeError as error:
		logger.error("Fallo en corrida ACP: %s", error)
		mensaje = str(error)
		if "429" in mensaje or "rate" in mensaje.lower():
			return JsonResponse({"error": mensaje}, status=429)
		return JsonResponse({"error": mensaje}, status=500)
