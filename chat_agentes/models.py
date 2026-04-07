"""Modelos persistentes del sistema de chat multiagente."""

from django.db import models


class Conversacion(models.Model):
	"""Representa una sesión persistente de conversación."""

	identificador_sesion = models.CharField(max_length=64, unique=True)
	titulo = models.CharField(max_length=120, default="Nueva conversación")
	mensaje_sistema = models.TextField()
	creada_en = models.DateTimeField(auto_now_add=True)
	actualizada_en = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-actualizada_en"]

	def __str__(self) -> str:
		return f"Conversación {self.id} - {self.titulo}"


class Mensaje(models.Model):
	"""Mensaje individual asociado a una conversación."""

	class Roles(models.TextChoices):
		SISTEMA = "system", "Sistema"
		USUARIO = "user", "Usuario"
		ASISTENTE = "assistant", "Asistente"

	conversacion = models.ForeignKey(
		Conversacion,
		related_name="mensajes",
		on_delete=models.CASCADE,
	)
	rol = models.CharField(max_length=16, choices=Roles.choices)
	contenido = models.TextField()
	orden = models.PositiveIntegerField()
	creado_en = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["orden", "id"]
		unique_together = ("conversacion", "orden")

	def __str__(self) -> str:
		return f"{self.rol} #{self.orden}"
