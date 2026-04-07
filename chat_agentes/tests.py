"""Pruebas de la arquitectura multiagente basada en Django."""

from django.test import TestCase

from chat_agentes.agentes import (
	AgenteControlador,
	AgenteEnrutadorTematico,
	AgenteRAG,
	AgenteVista,
	FragmentoRAG,
	OrquestadorChat,
)
from chat_agentes.models import Conversacion, Mensaje


class AgenteModeloFalso:
	"""Doble de pruebas para evitar llamadas reales al proveedor LLM."""

	def generar_respuesta(
		self,
		historial: list[dict[str, str]],
		instrucciones_agente: str,
		contexto_rag: list[FragmentoRAG],
	) -> str:
		ultimo_mensaje = historial[-1]["content"]
		tiene_rag = "sí" if contexto_rag else "no"
		marca = "Django" if "Django" in instrucciones_agente else "General"
		return f"[{marca}] Respuesta simulada a: {ultimo_mensaje} (RAG: {tiene_rag})"

	async def generar_respuesta_async(
		self,
		historial: list[dict[str, str]],
		instrucciones_agente: str,
		contexto_rag: list[FragmentoRAG],
	) -> str:
		return self.generar_respuesta(historial, instrucciones_agente, contexto_rag)


class AgenteRAGFalso:
	"""Doble de pruebas para controlar el contexto recuperado."""

	def buscar(self, consulta: str, max_resultados: int = 3) -> list[FragmentoRAG]:
		if "django" in consulta.lower():
			return [
				FragmentoRAG(
					fuente="django.md",
					contenido="Django usa ORM y migraciones.",
					puntaje=0.9,
				)
			]
		return []


class OrquestadorChatTests(TestCase):
	def setUp(self) -> None:
		self.orquestador = OrquestadorChat(
			agente_modelo=AgenteModeloFalso(),
			agente_vista=AgenteVista(),
			agente_controlador=AgenteControlador(),
			agente_rag=AgenteRAGFalso(),
			agente_enrutador=AgenteEnrutadorTematico(),
		)

	def test_crea_conversacion_y_mensaje_sistema_al_inicializar(self) -> None:
		contexto = self.orquestador.obtener_contexto_inicial("sesion-demo")

		conversacion = Conversacion.objects.get(identificador_sesion="sesion-demo")
		self.assertEqual(conversacion.mensajes.count(), 1)
		self.assertEqual(conversacion.mensajes.first().rol, Mensaje.Roles.SISTEMA)
		self.assertEqual(contexto["mensajes"], [])

	def test_procesar_mensaje_persiste_usuario_y_asistente(self) -> None:
		resultado = self.orquestador.procesar_mensaje("sesion-demo", "Hola agentes django")

		conversacion = resultado.conversacion
		mensajes = list(conversacion.mensajes.values_list("rol", "contenido"))

		self.assertEqual(len(mensajes), 3)
		self.assertEqual(mensajes[1][0], Mensaje.Roles.USUARIO)
		self.assertEqual(mensajes[1][1], "Hola agentes django")
		self.assertEqual(mensajes[2][0], Mensaje.Roles.ASISTENTE)
		self.assertIn("Respuesta simulada", mensajes[2][1])
		self.assertIn("RAG: sí", mensajes[2][1])

	def test_agente_vista_omite_mensaje_sistema(self) -> None:
		resultado = self.orquestador.procesar_mensaje("sesion-vista", "Prueba visual")
		mensajes = resultado.contexto["mensajes"]

		self.assertEqual(len(mensajes), 2)
		self.assertEqual(mensajes[0]["rol"], "user")
		self.assertEqual(mensajes[1]["rol"], "assistant")

	def test_enrutador_puede_activar_varios_agentes(self) -> None:
		enrutador = AgenteEnrutadorTematico()
		fragmentos = [
			FragmentoRAG(fuente="python.md", contenido="python listas funciones", puntaje=0.7),
			FragmentoRAG(fuente="ia_rag.md", contenido="rag orquestador agentes", puntaje=0.7),
		]
		agentes = enrutador.seleccionar_agentes(
			"Necesito ayuda con python y rag para agentes", fragmentos
		)
		self.assertGreaterEqual(len(agentes), 2)


class AgenteRAGTests(TestCase):
	def test_busca_fragmentos_desde_archivos(self) -> None:
		agente_rag = AgenteRAG()
		resultados = agente_rag.buscar("django migraciones orm", max_resultados=2)
		self.assertGreaterEqual(len(resultados), 1)
		self.assertTrue(any(item.fuente == "django.md" for item in resultados))
