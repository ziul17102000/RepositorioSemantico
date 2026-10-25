from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from repositorio_usuarios.decorators import rol_requerido
from repositorio_usuarios.models import RepositorioUser
from repositorio_usuarios.rbac import GROUP_ADMINS, GROUP_LIBRARIANS, GROUP_STUDENTS, user_in_group


@login_required
def dashboard_redirect(request):
	if request.user.is_superuser or user_in_group(request.user, GROUP_ADMINS):
		return redirect("repositorio_dashboard:admin")
	if user_in_group(request.user, GROUP_LIBRARIANS):
		return redirect("repositorio_dashboard:bibliotecario")
	if request.user.has_perm("repositorio_documentos.puede_avalar_documento"):
		return redirect("repositorio_documentos:avales")
	if request.user.has_perm("repositorio_documentos.puede_validar_academicamente"):
		return redirect("repositorio_documentos:validacion")
	if user_in_group(request.user, GROUP_STUDENTS):
		return redirect("repositorio_dashboard:estudiante")
	return redirect("repositorio_usuarios:login")


@rol_requerido(["administrador"])
def dashboard_admin(request):
	context = {
		"total_usuarios": RepositorioUser.objects.count(),
		"estudiantes_pendientes": RepositorioUser.objects.filter(groups__name=GROUP_STUDENTS, is_active=False).distinct().count(),
		"total_bibliotecarios": RepositorioUser.objects.filter(groups__name=GROUP_LIBRARIANS).distinct().count(),
	}
	return render(request, "repositorio_dashboard/dashboard_admin.html", context)


@rol_requerido(["bibliotecario"])
def dashboard_bibliotecario(request):
	pendientes = RepositorioUser.objects.filter(groups__name=GROUP_STUDENTS, is_active=False).distinct().count()
	return render(request, "repositorio_dashboard/dashboard_bibliotecario.html", {"estudiantes_pendientes": pendientes})


@rol_requerido(["estudiante"])
def dashboard_estudiante(request):
	return render(request, "repositorio_dashboard/dashboard_estudiante.html")
