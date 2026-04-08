#!/usr/bin/env bash
set -euo pipefail

# Uso:
#   DOMINIO=tu-dominio.com RUTA_PROYECTO=/opt/chatbot_con_memoria bash deploy/scripts/instalar_produccion.sh

DOMINIO="${DOMINIO:-example.com}"
RUTA_PROYECTO="${RUTA_PROYECTO:-/opt/chatbot_con_memoria}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ "${DOMINIO}" == "example.com" ]]; then
    echo "ERROR: Define DOMINIO con tu dominio real."
    exit 1
fi

if [[ ! -d "${RUTA_PROYECTO}" ]]; then
    echo "ERROR: No existe RUTA_PROYECTO=${RUTA_PROYECTO}"
    exit 1
fi

echo "[1/9] Instalando paquetes del sistema..."
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "[2/9] Creando entorno virtual..."
if [[ ! -d "${RUTA_PROYECTO}/.venv" ]]; then
    "${PYTHON_BIN}" -m venv "${RUTA_PROYECTO}/.venv"
fi

echo "[3/9] Instalando dependencias Python..."
"${RUTA_PROYECTO}/.venv/bin/pip" install --upgrade pip
"${RUTA_PROYECTO}/.venv/bin/pip" install -r "${RUTA_PROYECTO}/requirements.txt"

echo "[4/9] Ejecutando migraciones..."
DJANGO_DEBUG=false "${RUTA_PROYECTO}/.venv/bin/python" "${RUTA_PROYECTO}/manage.py" migrate --noinput

echo "[5/9] Recolectando estaticos..."
DJANGO_DEBUG=false "${RUTA_PROYECTO}/.venv/bin/python" "${RUTA_PROYECTO}/manage.py" collectstatic --noinput

echo "[6/9] Instalando servicio systemd..."
sudo sed \
    -e "s|__RUTA_PROYECTO__|${RUTA_PROYECTO}|g" \
    "${RUTA_PROYECTO}/deploy/systemd/chatbot_con_memoria.service" \
    > /tmp/chatbot_con_memoria.service
sudo mv /tmp/chatbot_con_memoria.service /etc/systemd/system/chatbot_con_memoria.service

sudo systemctl daemon-reload
sudo systemctl enable chatbot_con_memoria
sudo systemctl restart chatbot_con_memoria

echo "[7/9] Instalando configuracion Nginx..."
sudo sed \
    -e "s|__DOMINIO__|${DOMINIO}|g" \
    -e "s|__RUTA_PROYECTO__|${RUTA_PROYECTO}|g" \
    "${RUTA_PROYECTO}/deploy/nginx/chatbot_con_memoria.conf" \
    > /tmp/chatbot_con_memoria.nginx
sudo mv /tmp/chatbot_con_memoria.nginx /etc/nginx/sites-available/chatbot_con_memoria

if [[ ! -L /etc/nginx/sites-enabled/chatbot_con_memoria ]]; then
    sudo ln -s /etc/nginx/sites-available/chatbot_con_memoria /etc/nginx/sites-enabled/chatbot_con_memoria
fi

sudo nginx -t
sudo systemctl restart nginx

echo "[8/9] Emitiendo certificado TLS con certbot..."
sudo certbot --nginx -d "${DOMINIO}" --non-interactive --agree-tos -m "admin@${DOMINIO}" --redirect

echo "[9/9] Estado final..."
sudo systemctl --no-pager --full status chatbot_con_memoria | cat
sudo systemctl --no-pager --full status nginx | cat

echo "Despliegue completado: https://${DOMINIO}"
