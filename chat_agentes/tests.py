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

	def test_busqueda_sin_tokens_devuelve_lista_vacia(self) -> None:
		agente_rag = AgenteRAG()
		resultados = agente_rag.buscar("   ", max_resultados=3)
		self.assertEqual(resultados, [])

	def test_resultado_no_supera_max_resultados(self) -> None:
		agente_rag = AgenteRAG()
		resultados = agente_rag.buscar("python funciones lista", max_resultados=1)
		self.assertLessEqual(len(resultados), 1)

	def test_resultados_ordenados_por_puntaje_descendente(self) -> None:
		agente_rag = AgenteRAG()
		resultados = agente_rag.buscar("python django orm clase vista", max_resultados=5)
		puntajes = [item.puntaje for item in resultados]
		self.assertEqual(puntajes, sorted(puntajes, reverse=True))

	def test_tokenizar_normaliza_a_minusculas(self) -> None:
		tokens = AgenteRAG._tokenizar("Python Django ORM")
		self.assertIn("python", tokens)
		self.assertIn("django", tokens)
		self.assertIn("orm", tokens)

	def test_tokenizar_filtra_tokens_cortos(self) -> None:
		tokens = AgenteRAG._tokenizar("es un la lo de id")
		# Tokens menores de 3 caracteres se descartan
		self.assertEqual(tokens, set())


class AgenteEnrutadorTematicoTests(TestCase):
	def setUp(self) -> None:
		self.enrutador = AgenteEnrutadorTematico()

	def test_detecta_python(self) -> None:
		agentes = self.enrutador.seleccionar_agentes("funciones y listas en python", [])
		self.assertIn("python", agentes)

	def test_detecta_django(self) -> None:
		agentes = self.enrutador.seleccionar_agentes("como hacer migraciones en django", [])
		self.assertIn("django", agentes)

	def test_detecta_ia(self) -> None:
		agentes = self.enrutador.seleccionar_agentes("rag embeddings transformer llm", [])
		self.assertIn("ia", agentes)

	def test_fallback_general(self) -> None:
		agentes = self.enrutador.seleccionar_agentes("hola que tal esto", [])
		self.assertEqual(agentes, ["general"])

	def test_instrucciones_no_vacia_para_agentes_conocidos(self) -> None:
		for tema in ("python", "django", "ia", "general"):
			instrucciones = self.enrutador.instrucciones_para(tema)
			self.assertTrue(instrucciones.strip())

	def test_no_supera_tres_agentes(self) -> None:
		fragmentos = [
			FragmentoRAG(fuente="x.md", contenido="python django ia rag orm funciones", puntaje=0.9)
		]
		agentes = self.enrutador.seleccionar_agentes(
			"python django ia rag embeddings modelo clase", fragmentos
		)
		self.assertLessEqual(len(agentes), 3)


class LimpiarConversacionViewTests(TestCase):
	def test_limpiar_conversacion_elimina_mensajes_existentes(self) -> None:
		# Crear sesión y conversación de prueba
		self.client.get("/")
		session = self.client.session
		session.create()
		session.save()
		# Verificar que hay conversación
		response = self.client.post("/api/chat/limpiar/")
		self.assertEqual(response.status_code, 200)
		datos = response.json()
		self.assertTrue(datos.get("ok"))

	def test_limpiar_rechaza_get(self) -> None:
		response = self.client.get("/api/chat/limpiar/")
		self.assertEqual(response.status_code, 405)
