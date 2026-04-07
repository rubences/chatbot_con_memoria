"""Pruebas de la arquitectura multiagente basada en Django."""

from django.test import TestCase

from chat_agentes.agentes import AgenteControlador, AgenteVista, OrquestadorChat
from chat_agentes.models import Conversacion, Mensaje


class AgenteModeloFalso:
	"""Doble de pruebas para evitar llamadas reales al proveedor LLM."""

	def generar_respuesta(self, historial: list[dict[str, str]]) -> str:
		ultimo_mensaje = historial[-1]["content"]
		return f"Respuesta simulada a: {ultimo_mensaje}"


class OrquestadorChatTests(TestCase):
	def setUp(self) -> None:
		self.orquestador = OrquestadorChat(
			agente_modelo=AgenteModeloFalso(),
			agente_vista=AgenteVista(),
			agente_controlador=AgenteControlador(),
		)

	def test_crea_conversacion_y_mensaje_sistema_al_inicializar(self) -> None:
		contexto = self.orquestador.obtener_contexto_inicial("sesion-demo")

		conversacion = Conversacion.objects.get(identificador_sesion="sesion-demo")
		self.assertEqual(conversacion.mensajes.count(), 1)
		self.assertEqual(conversacion.mensajes.first().rol, Mensaje.Roles.SISTEMA)
		self.assertEqual(contexto["mensajes"], [])

	def test_procesar_mensaje_persiste_usuario_y_asistente(self) -> None:
		resultado = self.orquestador.procesar_mensaje("sesion-demo", "Hola agentes")

		conversacion = resultado.conversacion
		mensajes = list(conversacion.mensajes.values_list("rol", "contenido"))

		self.assertEqual(len(mensajes), 3)
		self.assertEqual(mensajes[1][0], Mensaje.Roles.USUARIO)
		self.assertEqual(mensajes[1][1], "Hola agentes")
		self.assertEqual(mensajes[2][0], Mensaje.Roles.ASISTENTE)
		self.assertIn("Respuesta simulada", mensajes[2][1])

	def test_agente_vista_omite_mensaje_sistema(self) -> None:
		resultado = self.orquestador.procesar_mensaje("sesion-vista", "Prueba visual")
		mensajes = resultado.contexto["mensajes"]

		self.assertEqual(len(mensajes), 2)
		self.assertEqual(mensajes[0]["rol"], "user")
		self.assertEqual(mensajes[1]["rol"], "assistant")
from django.test import TestCase

# Create your tests here.
