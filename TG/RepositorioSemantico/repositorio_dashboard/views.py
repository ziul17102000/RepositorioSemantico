from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from repositorio_usuarios.decorators import rol_requerido
from repositorio_usuarios.models import RepositorioUser


@login_required
def dashboard_redirect(request):
	destination = {
		"administrador": "repositorio_dashboard:admin",
		"bibliotecario": "repositorio_dashboard:bibliotecario",
		"estudiante": "repositorio_dashboard:estudiante",
	}.get(request.user.rol, "repositorio_usuarios:login")
	return redirect(destination)


@rol_requerido(["administrador"])
def dashboard_admin(request):
	context = {
		"total_usuarios": RepositorioUser.objects.count(),
		"estudiantes_pendientes": RepositorioUser.objects.filter(rol="estudiante", is_active=False).count(),
		"total_bibliotecarios": RepositorioUser.objects.filter(rol="bibliotecario").count(),
	}
	return render(request, "repositorio_dashboard/dashboard_admin.html", context)


@rol_requerido(["bibliotecario"])
def dashboard_bibliotecario(request):
	pendientes = RepositorioUser.objects.filter(rol="estudiante", is_active=False).count()
	return render(request, "repositorio_dashboard/dashboard_bibliotecario.html", {"estudiantes_pendientes": pendientes})


@rol_requerido(["estudiante"])
def dashboard_estudiante(request):
	return render(request, "repositorio_dashboard/dashboard_estudiante.html")
