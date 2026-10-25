from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .managers import RepositorioUserManager

nombre_validator = RegexValidator(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s'’-]+$", "Solo se permiten letras, espacios y guiones.")
cedula_validator = RegexValidator(r"^\d{6,12}$", "La cédula debe contener entre 6 y 12 números.")


class RepositorioUser(AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(unique=True)
	nombre_completo = models.CharField(max_length=180, blank=True, default="", validators=[nombre_validator])
	cedula = models.CharField(max_length=30, unique=True, null=True, blank=True, validators=[cedula_validator])
	is_active = models.BooleanField(default=False)
	is_staff = models.BooleanField(default=False)
	fecha_creacion = models.DateTimeField(default=timezone.now, editable=False)
	aprobado_por = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="estudiantes_aprobados")
	fecha_aprobacion = models.DateTimeField(null=True, blank=True)

	objects = RepositorioUserManager()

	USERNAME_FIELD = "email"
	REQUIRED_FIELDS = []

	class Meta:
		ordering = ["nombre_completo", "email"]
		verbose_name = "usuario del repositorio"
		verbose_name_plural = "usuarios del repositorio"

	def __str__(self):
		return f"{self.nombre_completo} ({self.email})"

	def get_full_name(self):
		return self.nombre_completo

	def get_short_name(self):
		return self.nombre_completo.split()[0] if self.nombre_completo else self.email


class Auditoria(models.Model):
	class Acciones(models.TextChoices):
		CREAR_USUARIO = "crear_usuario", "Crear usuario"
		ASIGNAR_GRUPO = "asignar_grupo", "Asignar grupo"
		APROBAR_ESTUDIANTE = "aprobar_estudiante", "Aprobar estudiante"
		APROBAR_DOCUMENTO = "aprobar_documento", "Aprobar documento"
		CAMBIAR_LICENCIA = "cambiar_licencia", "Cambiar licencias activas"

	usuario = models.ForeignKey(RepositorioUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="auditorias_realizadas")
	accion = models.CharField(max_length=40, choices=Acciones.choices)
	ip = models.GenericIPAddressField(null=True, blank=True)
	detalle = models.TextField(blank=True)
	fecha = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-fecha"]
		verbose_name = "registro de auditoría"
		verbose_name_plural = "registros de auditoría"

	def __str__(self):
		return f"{self.get_accion_display()} - {self.fecha:%Y-%m-%d %H:%M}"
