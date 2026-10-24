from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from repositorio_usuarios.decorators import rol_requerido
from .forms import DocumentoBaseForm, DocumentoEstudianteForm, DocumentoInstitucionalForm
from .models import Documento


def _documento_visible(request, documento):
	if documento.estado_revision == Documento.EstadoRevision.APROBADO:
		return True
	return request.user.is_authenticated and (documento.autor_id == request.user.pk or request.user.rol == "administrador")


def _client_ip(request):
	forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
	return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


def lista_documentos(request):
	documentos = Documento.objects.filter(estado_revision=Documento.EstadoRevision.APROBADO).select_related("autor")
	if request.user.is_authenticated:
		propios = Documento.objects.filter(autor=request.user).exclude(estado_revision=Documento.EstadoRevision.APROBADO).select_related("autor")
		documentos = (documentos | propios).distinct()
	return render(request, "repositorio_documentos/documento_list.html", {
		"documentos": documentos,
		"total_documentos": Documento.objects.filter(estado_revision=Documento.EstadoRevision.APROBADO).count(),
		"total_autores": Documento.objects.filter(estado_revision=Documento.EstadoRevision.APROBADO).values("autor").distinct().count(),
		"pendientes_propios": Documento.objects.filter(autor=request.user, estado_revision=Documento.EstadoRevision.PENDIENTE).count() if request.user.is_authenticated else 0,
	})


def detalle_documento(request, slug):
	documento = get_object_or_404(Documento.objects.select_related("autor"), url_permanente=slug)
	if not _documento_visible(request, documento):
		raise Http404
	return render(request, "repositorio_documentos/documento_detail.html", {"documento": documento})


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


@rol_requerido(["estudiante"])
def subir_documento_estudiante(request):
	form = DocumentoEstudianteForm(request.POST or None, request.FILES or None)
	if request.method == "POST" and form.is_valid():
		documento = form.save(commit=False)
		documento.autor = request.user
		documento.ip_registro = _client_ip(request)
		documento.save()
		messages.success(request, "Tu trabajo fue enviado y quedó pendiente de revisión.")
		return redirect(documento.get_absolute_url())
	return render(request, "repositorio_documentos/documento_upload_estudiante.html", {"form": form})


@rol_requerido(["bibliotecario", "administrador"])
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


@rol_requerido(["bibliotecario", "administrador"])
def lista_revision(request):
	documentos = Documento.objects.filter(estado_revision=Documento.EstadoRevision.PENDIENTE).select_related("autor")
	return render(request, "repositorio_documentos/revisar_documentos.html", {"documentos": documentos})


@require_POST
@rol_requerido(["bibliotecario", "administrador"])
def aprobar_documento(request, pk):
	documento = get_object_or_404(Documento, pk=pk, estado_revision=Documento.EstadoRevision.PENDIENTE)
	documento.estado_revision = Documento.EstadoRevision.APROBADO
	documento.save(update_fields=["estado_revision", "fecha_actualizacion"])
	messages.success(request, f"El documento '{documento.titulo}' fue aprobado.")
	return redirect("repositorio_documentos:revision")


@require_POST
@rol_requerido(["bibliotecario", "administrador"])
def rechazar_documento(request, pk):
	documento = get_object_or_404(Documento, pk=pk, estado_revision=Documento.EstadoRevision.PENDIENTE)
	documento.estado_revision = Documento.EstadoRevision.RECHAZADO
	documento.save(update_fields=["estado_revision", "fecha_actualizacion"])
	messages.info(request, f"El documento '{documento.titulo}' fue marcado como rechazado.")
	return redirect("repositorio_documentos:revision")


@login_required
def editar_documento(request, slug):
	documento = get_object_or_404(Documento, url_permanente=slug)
	if request.user.rol != "administrador" and documento.autor_id != request.user.pk:
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
	if request.user.rol != "administrador" and documento.autor_id != request.user.pk:
		return redirect("repositorio_documentos:lista")
	if request.method == "POST":
		documento.delete()
		messages.success(request, "El documento fue eliminado.")
		return redirect("repositorio_documentos:lista")
	return render(request, "repositorio_documentos/documento_confirm_delete.html", {"documento": documento})
