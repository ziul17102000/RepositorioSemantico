from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RepositorioUser


@admin.register(RepositorioUser)
class RepositorioUserAdmin(UserAdmin):
	ordering = ("email",)
	list_display = ("email", "nombre_completo", "rol", "is_active", "is_staff")
	list_filter = ("rol", "is_active", "is_staff")
	search_fields = ("email", "nombre_completo", "cedula")
	fieldsets = (
		(None, {"fields": ("email", "password")}),
		("Datos personales", {"fields": ("nombre_completo", "cedula", "rol")}),
		("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Aprobación", {"fields": ("aprobado_por", "fecha_aprobacion")}),
		("Fechas", {"fields": ("last_login", "fecha_creacion")}),
	)
	add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "nombre_completo", "cedula", "rol", "password1", "password2")}),)
	readonly_fields = ("fecha_creacion",)
	filter_horizontal = ("groups", "user_permissions")
