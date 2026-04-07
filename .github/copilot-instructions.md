# Instrucciones para GitHub Copilot

## Descripción del proyecto

`chatbot_con_memoria` es un chatbot en Python que mantiene memoria conversacional entre turnos, permitiendo al modelo recordar el historial de la sesión y ofrecer respuestas coherentes y contextuales.

## Stack tecnológico

- **Lenguaje:** Python 3.10+
- **LLM / API:** OpenAI (u otro proveedor compatible con la interfaz de chat)
- **Gestión de dependencias:** pip / `requirements.txt`
- **Entorno virtual:** venv o similar

## Convenciones del proyecto

- Todo el código debe estar en **español** (nombres de variables, comentarios, docstrings y mensajes al usuario).
- Seguir la guía de estilo **PEP 8**.
- Usar **type hints** en todas las funciones.
- Manejar errores con excepciones explícitas; evitar `except Exception` genérico sin registro.

## Estructura esperada del proyecto

```
chatbot_con_memoria/
├── .github/
│   └── copilot-instructions.md
├── src/
│   ├── chatbot.py        # Lógica principal del chatbot
│   ├── memoria.py        # Gestión del historial de conversación
│   └── config.py         # Configuración y variables de entorno
├── tests/
│   └── test_chatbot.py
├── requirements.txt
├── .env.example
└── README.md
```

## Patrones de implementación

- El historial de conversación se representa como una lista de diccionarios `{"role": ..., "content": ...}`.
- La memoria debe ser **acumulativa por sesión** y opcionalmente persistente (archivo JSON o base de datos SQLite).
- Las credenciales (API keys) se cargan exclusivamente desde **variables de entorno** mediante `python-dotenv`; nunca se incrustan en el código.

## Pruebas

- Usar **pytest** para las pruebas unitarias.
- Los tests deben cubrir al menos: inicialización del historial, adición de mensajes y truncamiento de memoria.

## Lo que Copilot debe evitar

- No incluir claves de API ni secretos en el código.
- No sugerir `print` para depuración en producción; usar el módulo `logging`.
- No usar librerías externas adicionales sin justificación clara.
