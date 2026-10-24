from django.contrib import admin

from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
	list_display = ("titulo", "autor", "tipo_trabajo", "estado_revision", "estado_acceso", "fecha_subida")
	list_filter = ("estado_revision", "estado_acceso", "tipo_trabajo", "licencia")
	search_fields = ("titulo", "autor__email", "autor__nombre_completo", "checksum_sha256")
	readonly_fields = ("url_permanente", "checksum_sha256", "fecha_subida", "fecha_actualizacion")
