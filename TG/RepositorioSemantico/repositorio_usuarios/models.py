from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import RepositorioUserManager


class RepositorioUser(AbstractBaseUser, PermissionsMixin):
	class Roles(models.TextChoices):
		ESTUDIANTE = "estudiante", "Estudiante"
		BIBLIOTECARIO = "bibliotecario", "Bibliotecario"
		ADMINISTRADOR = "administrador", "Administrador"

	email = models.EmailField(unique=True)
	nombre_completo = models.CharField(max_length=180, blank=True, default="")
	cedula = models.CharField(max_length=30, unique=True, null=True, blank=True)
	rol = models.CharField(max_length=20, choices=Roles.choices, default=Roles.ESTUDIANTE)
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
