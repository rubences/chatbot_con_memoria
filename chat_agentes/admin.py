from django.contrib import admin

from chat_agentes.models import Conversacion, Mensaje


class MensajeInline(admin.TabularInline):
	model = Mensaje
	extra = 0
	readonly_fields = ("rol", "contenido", "orden", "creado_en")


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
	list_display = ("id", "identificador_sesion", "titulo", "actualizada_en")
	search_fields = ("identificador_sesion", "titulo")
	inlines = [MensajeInline]


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
	list_display = ("id", "conversacion", "rol", "orden", "creado_en")
	list_filter = ("rol",)
	search_fields = ("contenido",)

# Register your models here.
