from django.core.validators import RegexValidator
from django.db import models


hex_color_validator = RegexValidator(regex=r"^#[0-9A-Fa-f]{6}$", message="Introduce un color hexadecimal válido, por ejemplo #16845B.")


class Configuracion(models.Model):
	nombre_universidad = models.CharField(max_length=180, default="Universidad")
	siglas = models.CharField(max_length=24, default="UNI")
	logo = models.ImageField(upload_to="configuracion/", blank=True, null=True)
	color_primario = models.CharField(max_length=7, default="#16845B", validators=[hex_color_validator])
	color_secundario = models.CharField(max_length=7, default="#123D34", validators=[hex_color_validator])
	correo_contacto = models.EmailField(blank=True)
	texto_terminos = models.TextField(blank=True, default="Al registrarme confirmo que los datos proporcionados son correctos.")
	permitir_registro_estudiantes = models.BooleanField(default=True)

	class Meta:
		verbose_name = "configuración institucional"
		verbose_name_plural = "configuración institucional"

	def __str__(self):
		return self.nombre_universidad

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		return None

	@classmethod
	def get_solo(cls):
		configuracion, _ = cls.objects.get_or_create(pk=1)
		return configuracion
