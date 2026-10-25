from django.contrib.auth.models import Group

from .models import Auditoria


GROUP_STUDENTS = "Estudiantes"
GROUP_TUTORS = "Tutores"
GROUP_COORDINATORS = "Coordinadores"
GROUP_LIBRARIANS = "Bibliotecarios"
GROUP_ADMINS = "Administradores"

INITIAL_GROUPS = (GROUP_STUDENTS, GROUP_TUTORS, GROUP_COORDINATORS, GROUP_LIBRARIANS, GROUP_ADMINS)

GROUP_PERMISSIONS = {
	GROUP_STUDENTS: {"repositorio_documentos.puede_crear_documento_propio", "repositorio_documentos.puede_ver_documentos_aprobados"},
	GROUP_TUTORS: {"repositorio_documentos.puede_avalar_documento"},
	GROUP_COORDINATORS: {"repositorio_documentos.puede_validar_academicamente"},
	GROUP_LIBRARIANS: {"repositorio_documentos.puede_publicar_documento"},
	GROUP_ADMINS: {"repositorio_documentos.puede_publicar_documento", "repositorio_documentos.puede_crear_documento_propio", "repositorio_documentos.puede_ver_documentos_aprobados"},
}


def user_in_group(user, group_name):
	return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name=group_name).exists()))


def user_is_admin(user):
	return bool(user and user.is_authenticated and (user.is_superuser or user.groups.filter(name=GROUP_ADMINS).exists()))


def ensure_group(group_name):
	return Group.objects.get_or_create(name=group_name)[0]


def group_names(user):
	if not user or not user.is_authenticated:
		return []
	return list(user.groups.values_list("name", flat=True))


def audit(user, action, request=None, detail=""):
	return Auditoria.objects.create(
		usuario=user if getattr(user, "is_authenticated", False) else None,
		accion=action,
		ip=(request.META.get("REMOTE_ADDR") if request else None),
		detalle=detail,
	)