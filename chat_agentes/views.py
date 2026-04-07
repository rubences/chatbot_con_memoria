"""Vistas Django para la interfaz del chatbot multiagente."""

from __future__ import annotations

import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from chat_agentes.agentes import ErrorConfiguracionModelo, OrquestadorChat


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
