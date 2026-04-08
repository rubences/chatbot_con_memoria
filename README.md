# chatbot_con_memoria

Chatbot con memoria conversacional que ahora incluye una arquitectura Django basada en tres agentes y un orquestador central.

https://medium.com/@jddam/gu%C3%ADa-completa-langgraph-y-el-futuro-de-los-agentes-de-ia-en-2025-2f34ceaa456f

## Arquitectura

- AgenteModelo: encapsula la comunicación con el proveedor LLM.
- AgenteVista: transforma la conversación persistida en contexto para la interfaz Django.
- AgenteControlador: administra la sesión, la persistencia y el historial en base de datos.
- OrquestadorChat: coordina a los tres agentes sin mezclar responsabilidades.

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

## Pruebas

Pruebas unitarias existentes:

```bash
pytest -q
```

Pruebas Django de la arquitectura multiagente:

```bash
python manage.py test
```