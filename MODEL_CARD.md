---
language:
  - es
tags:
  - chatbot
  - conversational
  - memory
  - multiagent
  - django
  - openai-compatible
  - huggingface
license: mit
pipeline_tag: text-generation
---

# memory-assistant-v1

Chatbot conversacional con memoria acumulativa por sesión y arquitectura multiagente basada en Django.

## Descripción

El modelo no es un peso entrenado, sino una aplicación completa que:

- Conecta con cualquier proveedor compatible con la API de OpenAI (OpenAI, Hugging Face Inference Router, Ollama, etc.).
- Mantiene el historial completo de conversación en cada turno para simular memoria en modelos stateless.
- Implementa una arquitectura de tres agentes independientes coordinados por un orquestador central.

## Arquitectura de agentes

| Agente | Responsabilidad |
|---|---|
| `AgenteModelo` | Comunicación exclusiva con el proveedor LLM |
| `AgenteVista` | Transformación del historial persistido para la interfaz Django |
| `AgenteControlador` | Gestión de sesión, persistencia y estado en base de datos |
| `OrquestadorChat` | Coordinación de los tres agentes sin mezclar responsabilidades |

## Uso rápido

```bash
# 1. Clonar el repositorio
git clone https://huggingface.co/rubences/memory-assistant-v1
cd memory-assistant-v1

# 2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu HF_API_KEY o OPENAI_API_KEY

# 5. Aplicar migraciones y arrancar
python manage.py migrate
python manage.py runserver
```

La interfaz principal queda disponible en http://127.0.0.1:8000/

## Proveedores soportados

```env
# Hugging Face Inference Router
PROVEEDOR=huggingface
HF_API_KEY=hf_tu_token_aqui
OPENAI_BASE_URL=https://router.huggingface.co/v1
MODELO=openai/gpt-oss-20b:fireworks-ai

# OpenAI
PROVEEDOR=openai
OPENAI_API_KEY=sk-tu_clave_aqui
MODELO=gpt-4o

# Ollama (local)
PROVEEDOR=openai
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
MODELO=llama3.2
```

## Tecnologías

- Python 3.10+
- Django 6.x + SQLite
- OpenAI Python SDK (compatible con cualquier endpoint `/v1`)
- Streamlit (interfaz alternativa en `src/chatbot.py`)
- pytest
