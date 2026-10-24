from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from repositorio_config.models import Configuracion
from .decorators import rol_requerido
from .forms import CrearBibliotecarioForm, LoginForm, RegistroEstudianteForm
from .models import RepositorioUser


def login_view(request):
	if request.user.is_authenticated:
		return redirect("repositorio_dashboard:inicio")
	form = LoginForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		email = form.cleaned_data["email"].strip().lower()
		user = authenticate(request, email=email, password=form.cleaned_data["password"])
		if user is not None:
			login(request, user)
			return redirect("repositorio_dashboard:inicio")
		if RepositorioUser.objects.filter(email__iexact=email, rol="estudiante", is_active=False).exists():
			messages.error(request, "Tu cuenta está pendiente de aprobación.")
		else:
			messages.error(request, "Correo o contraseña incorrectos.")
	return render(request, "repositorio_usuarios/login.html", {"form": form})


@require_POST
@login_required
def logout_view(request):
	logout(request)
	messages.info(request, "Sesión cerrada correctamente.")
	return redirect("repositorio_usuarios:login")


def registro_estudiante(request):
	configuracion = Configuracion.get_solo()
	if not configuracion.permitir_registro_estudiantes:
		messages.warning(request, "El registro de estudiantes está cerrado por el momento.")
		return redirect("repositorio_usuarios:login")
	form = RegistroEstudianteForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		try:
			form.save()
		except IntegrityError:
			form.add_error(None, "Ya existe una cuenta con esos datos. Verifica el correo y la cédula.")
		else:
			messages.success(request, "Tu cuenta está pendiente de aprobación.")
			return redirect("repositorio_usuarios:login")
	return render(request, "repositorio_usuarios/registro.html", {"form": form, "configuracion": configuracion})


@rol_requerido(["bibliotecario", "administrador"])
def lista_estudiantes_pendientes(request):
	estudiantes = RepositorioUser.objects.filter(rol="estudiante", is_active=False)
	return render(request, "repositorio_usuarios/pendientes.html", {"estudiantes": estudiantes})


@require_POST
@rol_requerido(["bibliotecario", "administrador"])
def aprobar_estudiante(request, pk):
	estudiante = get_object_or_404(RepositorioUser, pk=pk, rol="estudiante", is_active=False)
	estudiante.is_active = True
	estudiante.aprobado_por = request.user
	estudiante.fecha_aprobacion = timezone.now()
	estudiante.save(update_fields=["is_active", "aprobado_por", "fecha_aprobacion"])
	messages.success(request, f"La cuenta de {estudiante.nombre_completo} fue aprobada.")
	return redirect("repositorio_usuarios:pendientes")


@require_POST
@rol_requerido(["bibliotecario", "administrador"])
def rechazar_estudiante(request, pk):
	estudiante = get_object_or_404(RepositorioUser, pk=pk, rol="estudiante", is_active=False)
	nombre = estudiante.nombre_completo
	estudiante.delete()
	messages.success(request, f"La solicitud de {nombre} fue rechazada y eliminada.")
	return redirect("repositorio_usuarios:pendientes")


@rol_requerido(["administrador"])
def lista_usuarios(request):
	return render(request, "repositorio_usuarios/lista_usuarios.html", {"usuarios": RepositorioUser.objects.all()})


@rol_requerido(["administrador"])
def crear_bibliotecario(request):
	form = CrearBibliotecarioForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		try:
			bibliotecario = form.save()
		except IntegrityError:
			form.add_error(None, "Ya existe una cuenta con ese correo o cédula.")
		else:
			messages.success(request, f"Se creó la cuenta de {bibliotecario.nombre_completo}.")
			return redirect("repositorio_usuarios:usuarios")
	return render(request, "repositorio_usuarios/crear_bibliotecario.html", {"form": form})
