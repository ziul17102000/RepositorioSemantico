from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from repositorio_usuarios.decorators import grupo_requerido, rol_requerido
from repositorio_usuarios.rbac import GROUP_ADMINS, GROUP_COORDINATORS, GROUP_LIBRARIANS, GROUP_STUDENTS, GROUP_TUTORS, user_is_admin
from repositorio_usuarios.rbac import audit
from repositorio_config.models import Licencia
from .forms import DocumentoBaseForm, DocumentoEstudianteForm, DocumentoInstitucionalForm
from .models import Documento


def _documento_visible(request, documento):
	if documento.estado_revision == Documento.EstadoRevision.APROBADO:
		return True
	return request.user.is_authenticated and (documento.autor_id == request.user.pk or user_is_admin(request.user))


def _client_ip(request):
	forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
	return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


def lista_documentos(request):
	documentos = Documento.objects.filter(estado_revision=Documento.EstadoRevision.APROBADO).select_related("autor")
	if request.user.is_authenticated:
		propios = Documento.objects.filter(autor=request.user).exclude(estado_revision=Documento.EstadoRevision.APROBADO).select_related("autor")
		documentos = (documentos | propios).distinct()
	query = request.GET.get("q", "").strip()
	tipo = request.GET.get("tipo", "")
	anio = request.GET.get("anio", "")
	licencia = request.GET.get("licencia", "")
	if query:
		documentos = documentos.filter(Q(titulo__icontains=query) | Q(autor__nombre_completo__icontains=query) | Q(palabras_clave__icontains=query))
	if tipo:
		documentos = documentos.filter(tipo_trabajo=tipo)
	if anio:
		documentos = documentos.filter(fecha_defensa__year=anio)
	if licencia:
		documentos = documentos.filter(licencia=licencia)
	page_obj = Paginator(documentos, 12).get_page(request.GET.get("page"))
	return render(request, "repositorio_documentos/documento_list.html", {
		"documentos": page_obj,
		"page_obj": page_obj,
		"tipos_trabajo": Documento.TipoTrabajo.choices,
		"anios": Documento.objects.exclude(fecha_defensa=None).values_list("fecha_defensa__year", flat=True).distinct().order_by("-fecha_defensa__year"),
		"licencias": Documento.Licencias.choices,
		"filtros": {"q": query, "tipo": tipo, "anio": anio, "licencia": licencia},
		"total_documentos": Documento.objects.filter(estado_revision=Documento.EstadoRevision.APROBADO).count(),
		"total_autores": Documento.objects.filter(estado_revision=Documento.EstadoRevision.APROBADO).values("autor").distinct().count(),
		"pendientes_propios": Documento.objects.filter(autor=request.user, estado_revision=Documento.EstadoRevision.PENDIENTE).count() if request.user.is_authenticated else 0,
	})


def detalle_documento(request, slug):
	documento = get_object_or_404(Documento.objects.select_related("autor"), url_permanente=slug)
	if not _documento_visible(request, documento):
		raise Http404
	licencia = Licencia.objects.filter(codigo=documento.licencia).first()
	return render(request, "repositorio_documentos/documento_detail.html", {"documento": documento, "licencia": licencia})


def descargar_documento(request, slug):
	documento = get_object_or_404(Documento, url_permanente=slug)
	if not _documento_visible(request, documento):
		raise Http404
	if not documento.puede_descargar:
		messages.warning(request, "Este documento todavía no está disponible para descarga.")
		return redirect(documento.get_absolute_url())
	response = FileResponse(documento.archivo.open("rb"), content_type=documento.mime_type)
	response["Content-Disposition"] = f'attachment; filename="{documento.archivo.name.rsplit("/", 1)[-1]}"'
	return response


@grupo_requerido([GROUP_STUDENTS], "repositorio_documentos.puede_crear_documento_propio")
def subir_documento_estudiante(request):
	form = DocumentoEstudianteForm(request.POST or None, request.FILES or None)
	if request.method == "POST" and form.is_valid():
		documento = form.save(commit=False)
		documento.autor = request.user
		documento.ip_registro = _client_ip(request)
		documento.save()
		messages.success(request, "Tu trabajo fue enviado y quedó pendiente de revisión bibliotecaria.")
		return redirect(documento.get_absolute_url())
	return render(request, "repositorio_documentos/documento_upload_estudiante.html", {"form": form})


@grupo_requerido([GROUP_LIBRARIANS, GROUP_ADMINS], "repositorio_documentos.puede_publicar_documento")
def subir_documento_institucional(request):
	form = DocumentoInstitucionalForm(request.POST or None, request.FILES or None)
	if request.method == "POST" and form.is_valid():
		documento = form.save(commit=False)
		documento.autor = form.cleaned_data.get("autor") or request.user
		documento.ip_registro = _client_ip(request)
		documento.save()
		messages.success(request, "El documento institucional fue publicado.")
		return redirect(documento.get_absolute_url())
	return render(request, "repositorio_documentos/documento_upload_institucional.html", {"form": form})


@grupo_requerido([GROUP_LIBRARIANS, GROUP_ADMINS], "repositorio_documentos.puede_publicar_documento")
def lista_revision(request):
	documentos = Documento.objects.filter(estado_revision=Documento.EstadoRevision.PENDIENTE).select_related("autor")
	return render(request, "repositorio_documentos/revisar_documentos.html", {"documentos": documentos})


@require_POST
@grupo_requerido([GROUP_LIBRARIANS, GROUP_ADMINS], "repositorio_documentos.puede_publicar_documento")
def aprobar_documento(request, pk):
	documento = get_object_or_404(Documento, pk=pk, estado_revision=Documento.EstadoRevision.PENDIENTE)
	documento.estado_revision = Documento.EstadoRevision.APROBADO
	documento.save(update_fields=["estado_revision", "fecha_actualizacion"])
	audit(request.user, "aprobar_documento", request, f"Publicó documento {documento.pk}: {documento.titulo}")
	messages.success(request, f"El documento '{documento.titulo}' fue aprobado.")
	return redirect("repositorio_documentos:revision")


@require_POST
@grupo_requerido([GROUP_LIBRARIANS, GROUP_ADMINS], "repositorio_documentos.puede_publicar_documento")
def rechazar_documento(request, pk):
	documento = get_object_or_404(Documento, pk=pk, estado_revision=Documento.EstadoRevision.PENDIENTE)
	documento.estado_revision = Documento.EstadoRevision.RECHAZADO
	documento.save(update_fields=["estado_revision", "fecha_actualizacion"])
	messages.info(request, f"El documento '{documento.titulo}' fue marcado como rechazado.")
	return redirect("repositorio_documentos:revision")


@login_required
def editar_documento(request, slug):
	documento = get_object_or_404(Documento, url_permanente=slug)
	if not user_is_admin(request.user) and documento.autor_id != request.user.pk:
		return redirect("repositorio_documentos:lista")
	form = DocumentoBaseForm(request.POST or None, request.FILES or None, instance=documento)
	if request.method == "POST" and form.is_valid():
		edited = form.save(commit=False)
		edited.autor = documento.autor
		edited.metodo_ingreso = documento.metodo_ingreso
		edited.estado_revision = documento.estado_revision
		edited.acepto_terminos = documento.acepto_terminos
		edited.autorizo_preservacion = documento.autorizo_preservacion
		edited.save()
		messages.success(request, "El documento fue actualizado.")
		return redirect(edited.get_absolute_url())
	return render(request, "repositorio_documentos/documento_edit.html", {"form": form, "documento": documento})


@login_required
def eliminar_documento(request, slug):
	documento = get_object_or_404(Documento, url_permanente=slug)
	if not user_is_admin(request.user) and documento.autor_id != request.user.pk:
		return redirect("repositorio_documentos:lista")
	if request.method == "POST":
		documento.delete()
		messages.success(request, "El documento fue eliminado.")
		return redirect("repositorio_documentos:lista")
	return render(request, "repositorio_documentos/documento_confirm_delete.html", {"documento": documento})


@grupo_requerido([GROUP_TUTORS], "repositorio_documentos.puede_avalar_documento")
def lista_avales(request):
	documentos = Documento.objects.filter(tutor_asignado=request.user).select_related("autor")
	return render(request, "repositorio_documentos/revisar_academico.html", {"documentos": documentos, "modo": "aval"})


@require_POST
@grupo_requerido([GROUP_TUTORS], "repositorio_documentos.puede_avalar_documento")
def avalar_documento(request, pk):
	documento = get_object_or_404(Documento, pk=pk, tutor_asignado=request.user)
	documento.estado_aval = Documento.EstadoProceso.APROBADO
	documento.avalado_por = request.user
	documento.fecha_aval = timezone.now()
	documento.save(update_fields=["estado_aval", "avalado_por", "fecha_aval", "fecha_actualizacion"])
	messages.success(request, "El documento fue avalado por el tutor.")
	return redirect("repositorio_documentos:avales")


@grupo_requerido([GROUP_COORDINATORS], "repositorio_documentos.puede_validar_academicamente")
def lista_validacion_academica(request):
	documentos = Documento.objects.filter(estado_aval=Documento.EstadoProceso.APROBADO).select_related("autor", "tutor_asignado")
	return render(request, "repositorio_documentos/revisar_academico.html", {"documentos": documentos, "modo": "validacion"})


@require_POST
@grupo_requerido([GROUP_COORDINATORS], "repositorio_documentos.puede_validar_academicamente")
def validar_academicamente(request, pk):
	documento = get_object_or_404(Documento, pk=pk, estado_aval=Documento.EstadoProceso.APROBADO)
	documento.estado_validacion_academica = Documento.EstadoProceso.APROBADO
	documento.validado_por = request.user
	documento.fecha_validacion_academica = timezone.now()
	documento.save(update_fields=["estado_validacion_academica", "validado_por", "fecha_validacion_academica", "fecha_actualizacion"])
	messages.success(request, "El documento fue validado académicamente.")
	return redirect("repositorio_documentos:validacion")
