# chatbot_con_memoria

Chatbot con memoria conversacional que ahora incluye una arquitectura Django basada en tres agentes y un orquestador central.

https://medium.com/@jddam/gu%C3%ADa-completa-langgraph-y-el-futuro-de-los-agentes-de-ia-en-2025-2f34ceaa456f

## Arquitectura

- AgenteModelo: encapsula la comunicación con el proveedor LLM.
- AgenteVista: transforma la conversación persistida en contexto para la interfaz Django.
- AgenteControlador: administra la sesión, la persistencia y el historial en base de datos.
- OrquestadorChat: coordina a los tres agentes sin mezclar responsabilidades.

## Módulo de análisis de call center (CrewAI)

El proyecto incorpora un flujo multiagente para analizar transcripciones de atención al cliente.

Equipo colaborativo implementado:

- Analizador de Transcripciones
- Especialista en Control de Calidad (QA)
- Generador de Informes

Flujo de tareas secuencial:

1. El Analizador extrae hallazgos, sentimiento y palabras clave.
2. El Especialista QA evalúa métricas de calidad (CSAT, CES, NPS, FCR y protocolo).
3. El Generador compila un informe ejecutivo con recomendaciones accionables.

Herramientas personalizadas incluidas:

- Herramienta de Análisis de Sentimientos
- Herramienta de Extracción de Palabras Clave

Puntos de entrada:

- Web: `/analisis/`
- CLI: `python manage.py analizar_llamada [ruta_transcripcion] --salida informe.md`

Estrategias disponibles en el modulo de analisis:

- `crewai`: equipo por roles (Analizador, QA, Generador).
- `rewoo`: pipeline planificador/trabajador/solucionador.

Ejemplos:

```bash
# Estrategia CrewAI
python manage.py analizar_llamada --estrategia crewai

# Estrategia ReWOO
python manage.py analizar_llamada --estrategia rewoo

# ReWOO + busqueda web (Serper)
python manage.py analizar_llamada --estrategia rewoo --busqueda-web
```

En la interfaz `/analisis/`, si eliges `ReWOO`, puedes activar la casilla de búsqueda web para usar Serper durante el paso de trabajador.

## Persistencia

La base de datos usa SQLite mediante Django ORM con dos modelos:

- Conversacion
- Mensaje

## Arranque de la versión Django

1. Activa el entorno virtual.
2. Copia .env.example a .env y configura tu proveedor.
3. Ejecuta las migraciones.
4. Inicia el servidor.

Comandos:

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

La interfaz principal queda disponible en la ruta raíz.

## Despliegue en producción

Pasos recomendados:

1. Configura `.env` con `DJANGO_DEBUG=false` y hosts reales en `DJANGO_ALLOWED_HOSTS`.
2. Instala dependencias.
3. Aplica migraciones.
4. Recolecta estáticos.
5. Ejecuta `gunicorn` con el módulo WSGI.

Comandos:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn configuracion.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
```

Notas de seguridad:

- Define un `DJANGO_SECRET_KEY` robusto en producción.
- Si terminas TLS en un proxy (Nginx/Traefik), mantén `X-Forwarded-Proto` habilitado.
- Ajusta `DJANGO_CSRF_TRUSTED_ORIGINS` al dominio real (por ejemplo, `https://tu-dominio.com`).

### Produccion con systemd + Nginx + TLS

Se incluyen plantillas y un script en:

- `deploy/systemd/chatbot_con_memoria.service`
- `deploy/nginx/chatbot_con_memoria.conf`
- `deploy/scripts/instalar_produccion.sh`

Requisitos en servidor Linux:

1. El proyecto debe estar en una ruta fija (por ejemplo, `/opt/chatbot_con_memoria`).
2. DNS del dominio apuntando al servidor.
3. Puerto 80/443 abierto.

Ejemplo de ejecución:

```bash
cd /opt/chatbot_con_memoria
DOMINIO=tu-dominio.com RUTA_PROYECTO=/opt/chatbot_con_memoria bash deploy/scripts/instalar_produccion.sh
```

El script hace:

1. Instala Nginx y certbot.
2. Crea/actualiza entorno virtual e instala dependencias.
3. Ejecuta migraciones y `collectstatic`.
4. Instala servicio systemd de Gunicorn.
5. Instala sitio Nginx.
6. Emite certificado TLS y activa redirección a HTTPS.

## Configuración de CrewAI

Instalación recomendada:

```bash
source .venv/bin/activate
pip install "crewai[tools]"
```

Variables relevantes en `.env`:

- `PROVEEDOR`
- `OPENAI_API_KEY` y/o `HF_API_KEY`
- `OPENAI_BASE_URL`
- `MODELO`
- `TEMPERATURA`
- `SERPER_API_KEY` (opcional, para búsqueda web en ReWOO)
- `OPENROUTER_API_KEY` (si `PROVEEDOR=openrouter`)
- `REWOO_MAX_REINTENTOS_429` (opcional, por defecto `3`)
- `REWOO_BACKOFF_INICIAL_SEGUNDOS` (opcional, por defecto `1.5`)

Nota: el equipo CrewAI reutiliza la misma configuración de modelo definida en `src/config.py`.

### Configuración rápida para OpenRouter

```bash
PROVEEDOR=openrouter
OPENROUTER_API_KEY=sk-or-...tu-clave...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODELO=meta-llama/llama-3.3-70b-instruct:free
```

Si recibes errores `402` (sin créditos) o `429` (rate limit), cambia a otro modelo `:free` o reintenta más tarde.
ReWOO aplica retry exponencial automático para `429` antes de devolver error final.

## ACP en este proyecto

Se añadió un endpoint de interoperabilidad inspirado en ACP:

- `POST /api/acp/run/`

Formato de mensaje (JSON):

```json
{
	"message": {
		"role": "user",
		"parts": [
			{
				"content": "<transcripcion de llamada>",
				"content_type": "text/plain"
			}
		],
		"metadata": {
			"estrategia": "rewoo",
			"usar_busqueda_web": true
		}
	}
}
```

Ejemplo con `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/acp/run/ \
	-H "Content-Type: application/json" \
	-d '{
		"message": {
			"role": "user",
			"parts": [{"content": "Transcripción de ejemplo...", "content_type": "text/plain"}],
			"metadata": {"estrategia": "rewoo", "usar_busqueda_web": true}
		}
	}'
```

Respuesta:

- `input_message`: mensaje ACP recibido.
- `output_message`: mensaje ACP generado por el agente.
- `run_status`: estado de ejecución.

## Estrategias de colaboración multiagente

### 1) Colaboración basada en reglas

Definición:

- Las interacciones se controlan mediante reglas explícitas (if/else, estados, lógica determinista).
- Se prioriza consistencia y predictibilidad sobre adaptabilidad.

Pros:

- Alta eficiencia en tareas estructuradas.
- Comportamiento estable y auditable.

Contras:

- Baja flexibilidad ante cambios del entorno.
- Escala peor en escenarios ambiguos o dinámicos.

### 2) Colaboración basada en roles

Definición:

- Cada agente tiene responsabilidades especializadas y límites claros.
- Los agentes colaboran compartiendo contexto para cumplir un objetivo común.

Pros:

- Modularidad y separación de responsabilidades.
- Mejora de calidad por especialización.

Contras:

- Dependencia de una buena integración/orquestación.
- Menor flexibilidad si los roles están demasiado rígidos.

Aplicación en este proyecto:

- Es la estrategia principal del sistema (Analizador, QA y Generador de Informes).

### 3) Colaboración basada en modelos

Definición:

- Los agentes actualizan creencias internas y razonan bajo incertidumbre.
- Se apoyan en inferencia probabilística, planificación y aprendizaje.

Pros:

- Alta capacidad de adaptación y decisiones contextuales.
- Mejor rendimiento cuando hay información incompleta.

Contras:

- Mayor complejidad de diseño y coste computacional.
- Requiere más control y observabilidad en producción.

## Metodología ReWOO

ReWOO (Reasoning WithOut Observation overload) separa el razonamiento en módulos para reducir consumo de tokens y mejorar la calidad de respuesta con herramientas externas.

Componentes principales:

1. Planificador:
	divide una tarea compleja en subpreguntas concretas y ordenadas.

2. Trabajador:
	consulta herramientas externas (por ejemplo, buscador web, base de datos, APIs) para reunir evidencia de cada subpregunta.

3. Solucionador:
	sintetiza toda la evidencia recuperada en una respuesta final coherente y estructurada.

Ventajas de ReWOO:

- Menos repeticiones de instrucciones al LLM.
- Mayor control del flujo de razonamiento.
- Mejor escalabilidad en tareas largas o con conocimiento externo.

Limitaciones:

- Requiere diseñar bien el planificador y las subpreguntas.
- Depende de la calidad de las herramientas externas.
- Incrementa la complejidad de orquestación.

### Aplicación de ReWOO en este proyecto

La adaptación recomendada para este repositorio es:

1. Planificador:
	para una tarea como "analizar una llamada", generar subpreguntas como tono, riesgo de escalada, métricas de calidad y recomendaciones.

2. Trabajador:
	usar herramientas de recuperación (RAG local, búsqueda externa opcional, métricas de QA) para responder cada subpregunta con evidencia.

3. Solucionador:
	combinar los hallazgos en un informe final para supervisores y gestores.

Esto complementa la arquitectura por roles ya implementada (Analizador, QA, Generador), aportando un patrón explícito de razonamiento paso a paso.

### Tecnologías típicas para ReWOO

- LLMs de instrucciones (OpenAI, IBM Granite, otros compatibles).
- Librerías de inferencia y orquestación (Transformers, LangChain, LangGraph).
- Herramientas de recuperación en tiempo real (Serper, Tavily, RAG local).

### Flujo mínimo de implementación

1. Crear función planner(task) para generar subpreguntas.
2. Crear función worker(question) para recuperar contexto con herramientas.
3. Crear función solver(task, evidencias) para sintetizar resultado final.
4. Añadir validación, límites de tokens y manejo de errores de red.

Referencia de contenido base proporcionada por el usuario:

- `7dd18e2df2ece3986a17c6a6fe2a5569a40b3e56`

## Marcos multiagente relevantes

1. IBM Bee Agent Framework:
	enfoque modular orientado a producción con estado serializable y control de procesos escalables.

2. LangChain Agents:
	ecosistema amplio para razonamiento con herramientas, flujos de varios pasos e integraciones.

3. OpenAI Swarm:
	coordinación ligera mediante rutinas y handoffs entre agentes especializados.

4. CrewAI (usado en este proyecto):
	definición clara de agentes, tareas, herramientas y ejecución secuencial/paralela con configuración simple.

## Soluciones empresariales: watsonx Orchestrate

Un enfoque empresarial multiagente suele incluir:

- Registro de habilidades (catálogo de capacidades).
- Analizador de intenciones para enrutar solicitudes.
- Orquestador de flujos con secuencias, ramificaciones, reintentos y manejo de errores.
- Memoria/contexto compartido para continuidad entre agentes.
- Supervisión humana opcional (human-in-the-loop).

Estas piezas son una referencia útil para evolucionar este proyecto hacia flujos de negocio más complejos.

## Predicciones y roadmap

Dirección esperada para sistemas multiagente:

- Inteligencia colectiva emergente mediante colaboración especializada.
- Mejoras incrementales en precisión, relevancia y coherencia global.
- Mayor uso de descomposición de tareas para resolver problemas complejos.

Próximos pasos sugeridos para este repositorio:

1. Añadir evaluación automática del informe generado (rúbricas de calidad).
2. Incorporar trazabilidad de tareas/agentes con logs estructurados por ejecución.
3. Soportar procesos híbridos (secuencial + paralelo) para reducir latencia.
4. Añadir panel de métricas históricas por lote de transcripciones.

## Pruebas

Pruebas unitarias existentes:

```bash
pytest -q
```

Pruebas Django de la arquitectura multiagente:

```bash
python manage.py test
```