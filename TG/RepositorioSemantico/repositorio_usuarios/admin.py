from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import RepositorioUser

admin.site.unregister(Group)


@admin.register(RepositorioUser)
class RepositorioUserAdmin(UserAdmin):
	ordering = ("email",)
	list_display = ("email", "nombre_completo", "is_active", "is_staff", "grupos_actuales")
	list_filter = ("is_active", "is_staff", "groups")
	search_fields = ("email", "nombre_completo", "cedula")
	fieldsets = (
		(None, {"fields": ("email", "password")}),
		("Datos personales", {"fields": ("nombre_completo", "cedula")}),
		("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
		("Aprobación", {"fields": ("aprobado_por", "fecha_aprobacion")}),
		("Fechas", {"fields": ("last_login", "fecha_creacion")}),
	)
	add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "nombre_completo", "cedula", "password1", "password2")}),)
	readonly_fields = ("fecha_creacion",)
	filter_horizontal = ("groups", "user_permissions")

	@admin.display(description="Grupos")
	def grupos_actuales(self, obj):
		return ", ".join(obj.groups.values_list("name", flat=True)) or "Sin grupo"


@admin.register(Group)
class RepositorioGroupAdmin(admin.ModelAdmin):
	search_fields = ("name",)
	filter_horizontal = ("permissions",)

	def has_module_permission(self, request):
		return request.user.is_superuser

	def has_view_permission(self, request, obj=None):
		return request.user.is_superuser

	def has_add_permission(self, request):
		return request.user.is_superuser

	def has_change_permission(self, request, obj=None):
		return request.user.is_superuser

	def has_delete_permission(self, request, obj=None):
		return request.user.is_superuser
