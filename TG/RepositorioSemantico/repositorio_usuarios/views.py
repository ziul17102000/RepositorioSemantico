from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from repositorio_config.models import Configuracion
from django.contrib.auth.models import Group

from .decorators import grupo_requerido, rol_requerido
from .forms import CambiarGruposForm, CrearBibliotecarioForm, CrearUsuarioForm, GrupoPermisosForm, LoginForm, RegistroEstudianteForm
from .models import RepositorioUser
from .rbac import GROUP_ADMINS, GROUP_LIBRARIANS, GROUP_STUDENTS, audit, ensure_group


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
		if RepositorioUser.objects.filter(email__iexact=email, groups__name=GROUP_STUDENTS, is_active=False).exists():
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
	estudiantes = RepositorioUser.objects.filter(groups__name=GROUP_STUDENTS, is_active=False).distinct()
	return render(request, "repositorio_usuarios/pendientes.html", {"estudiantes": estudiantes})


@require_POST
@rol_requerido(["bibliotecario", "administrador"])
def aprobar_estudiante(request, pk):
	estudiante = get_object_or_404(RepositorioUser, pk=pk, groups__name=GROUP_STUDENTS, is_active=False)
	estudiante.is_active = True
	estudiante.aprobado_por = request.user
	estudiante.fecha_aprobacion = timezone.now()
	estudiante.save(update_fields=["is_active", "aprobado_por", "fecha_aprobacion"])
	audit(request.user, "aprobar_estudiante", request, f"Aprobó estudiante {estudiante.email}")
	messages.success(request, f"La cuenta de {estudiante.nombre_completo} fue aprobada.")
	return redirect("repositorio_usuarios:pendientes")


@require_POST
@rol_requerido(["bibliotecario", "administrador"])
def rechazar_estudiante(request, pk):
	estudiante = get_object_or_404(RepositorioUser, pk=pk, groups__name=GROUP_STUDENTS, is_active=False)
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


@grupo_requerido([GROUP_ADMINS])
def gestion_usuarios(request):
	usuarios = RepositorioUser.objects.prefetch_related("groups")
	return render(request, "repositorio_usuarios/gestion_usuarios.html", {"usuarios": usuarios})


@grupo_requerido([GROUP_ADMINS])
def crear_usuario(request):
	form = CrearUsuarioForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		usuario = form.save()
		audit(request.user, "crear_usuario", request, f"Creó usuario {usuario.email}")
		messages.success(request, f"Usuario {usuario.email} creado correctamente.")
		return redirect("repositorio_usuarios:gestion_usuarios")
	return render(request, "repositorio_usuarios/crear_usuario.html", {"form": form})


@grupo_requerido([GROUP_ADMINS])
def cambiar_grupos_usuario(request, pk):
	usuario = get_object_or_404(RepositorioUser, pk=pk)
	form = CambiarGruposForm(request.POST or None, user=usuario)
	if request.method == "POST" and form.is_valid():
		grupos = list(form.cleaned_data["grupos"])
		usuario.groups.set(grupos)
		audit(request.user, "asignar_grupo", request, f"Asignó grupos a {usuario.email}: {', '.join(group.name for group in grupos) or 'ninguno'}")
		messages.success(request, "Los grupos del usuario fueron actualizados.")
		return redirect("repositorio_usuarios:gestion_usuarios")
	return render(request, "repositorio_usuarios/cambiar_grupos.html", {"form": form, "usuario": usuario})


@grupo_requerido([GROUP_ADMINS])
def detalle_grupo(request, pk):
	grupo = get_object_or_404(Group, pk=pk)
	if request.user.is_superuser:
		form = GrupoPermisosForm(request.POST or None, instance=grupo)
		if request.method == "POST" and form.is_valid():
			form.save()
			messages.success(request, "Los permisos técnicos del grupo fueron actualizados.")
			return redirect("repositorio_usuarios:detalle_grupo", pk=grupo.pk)
	else:
		form = None
	return render(request, "repositorio_usuarios/detalle_grupo.html", {"grupo": grupo, "form": form, "puede_editar": request.user.is_superuser})
