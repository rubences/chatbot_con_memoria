"""Rutas de la app chat_agentes."""

from django.urls import path

from chat_agentes import views

app_name = "chat_agentes"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("api/chat/", views.enviar_mensaje, name="enviar_mensaje"),
    path("api/chat/limpiar/", views.limpiar_conversacion, name="limpiar_conversacion"),
]

urlpatterns += [
    path("analisis/", views.analisis_llamada, name="analisis_llamada"),
]