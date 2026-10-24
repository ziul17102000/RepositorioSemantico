import hashlib
import mimetypes
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Documento(models.Model):
	class TipoTrabajo(models.TextChoices):
		TESIS = "tesis", "Tesis"
		TRABAJO_GRADO = "trabajo_grado", "Trabajo de grado"
		MONOGRAFIA = "monografia", "Monografía"
		PROYECTO = "proyecto", "Proyecto"
		ARTICULO = "articulo", "Artículo académico"

	class Licencias(models.TextChoices):
		CC0 = "cc0", "CC0 1.0 Universal"
		CC_BY = "cc_by", "CC BY 4.0"
		CC_BY_SA = "cc_by_sa", "CC BY-SA 4.0"
		CC_BY_NC = "cc_by_nc", "CC BY-NC 4.0"
		CC_BY_NC_SA = "cc_by_nc_sa", "CC BY-NC-SA 4.0"
		CC_BY_ND = "cc_by_nd", "CC BY-ND 4.0"
		CC_BY_NC_ND = "cc_by_nc_nd", "CC BY-NC-ND 4.0"

	class MetodoIngreso(models.TextChoices):
		AUTODEPOSITO = "autodeposito", "Autodepósito"
		CARGA_INSTITUCIONAL = "carga_institucional", "Carga institucional"

	class EstadoAcceso(models.TextChoices):
		ABIERTO = "abierto", "Abierto"
		EMBARGADO = "embargado", "Embargado"
		RESTRINGIDO = "restringido", "Restringido"

	class EstadoRevision(models.TextChoices):
		PENDIENTE = "pendiente", "Pendiente"
		APROBADO = "aprobado", "Aprobado"
		RECHAZADO = "rechazado", "Rechazado"

	titulo = models.CharField(max_length=250)
	autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documentos")
	tutor = models.CharField(max_length=180, blank=True)
	resumen = models.TextField()
	fecha_defensa = models.DateField(null=True, blank=True)
	tipo_trabajo = models.CharField(max_length=30, choices=TipoTrabajo.choices)
	idioma = models.CharField(max_length=10, default="es")
	palabras_clave = models.CharField(max_length=500, help_text="Separa las palabras clave con comas.")
	url_permanente = models.SlugField(max_length=280, unique=True, blank=True)
	archivo = models.FileField(upload_to="documentos/%Y/%m/", validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx", "jpg", "jpeg", "png", "webp"])])
	checksum_sha256 = models.CharField(max_length=64, blank=True)
	licencia = models.CharField(max_length=20, choices=Licencias.choices, default=Licencias.CC_BY)
	fecha_aceptacion_licencia = models.DateTimeField(null=True, blank=True)
	ip_registro = models.GenericIPAddressField(null=True, blank=True)
	metodo_ingreso = models.CharField(max_length=25, choices=MetodoIngreso.choices, default=MetodoIngreso.AUTODEPOSITO)
	acepto_terminos = models.BooleanField(default=False)
	autorizo_preservacion = models.BooleanField(default=False)
	estado_acceso = models.CharField(max_length=20, choices=EstadoAcceso.choices, default=EstadoAcceso.ABIERTO)
	fecha_liberacion = models.DateTimeField(null=True, blank=True)
	estado_revision = models.CharField(max_length=20, choices=EstadoRevision.choices, default=EstadoRevision.PENDIENTE)
	fecha_subida = models.DateTimeField(default=timezone.now, editable=False)
	fecha_actualizacion = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-fecha_subida"]
		verbose_name = "documento"
		verbose_name_plural = "documentos"

	def __str__(self):
		return self.titulo

	def save(self, *args, **kwargs):
		if not self.url_permanente:
			base_slug = slugify(self.titulo)[:260] or "documento"
			candidate, suffix = base_slug, 2
			while Documento.objects.filter(url_permanente=candidate).exclude(pk=self.pk).exists():
				candidate = f"{base_slug[:250]}-{suffix}"
				suffix += 1
			self.url_permanente = candidate
		if self.archivo and not self.checksum_sha256:
			current_position = self.archivo.tell() if hasattr(self.archivo, "tell") else 0
			self.archivo.seek(0)
			digest = hashlib.sha256()
			for chunk in self.archivo.chunks():
				digest.update(chunk)
			self.checksum_sha256 = digest.hexdigest()
			self.archivo.seek(current_position)
		if self.acepto_terminos and not self.fecha_aceptacion_licencia:
			self.fecha_aceptacion_licencia = timezone.now()
		super().save(*args, **kwargs)

	@property
	def extension(self):
		return Path(self.archivo.name).suffix.lower().lstrip(".") if self.archivo else ""

	@property
	def es_pdf(self):
		return self.extension == "pdf"

	@property
	def es_docx(self):
		return self.extension == "docx"

	@property
	def es_imagen(self):
		return self.extension in {"jpg", "jpeg", "png", "webp"}

	@property
	def puede_descargar(self):
		if self.estado_revision != self.EstadoRevision.APROBADO:
			return False
		if self.estado_acceso == self.EstadoAcceso.EMBARGADO:
			return bool(self.fecha_liberacion and timezone.now() >= self.fecha_liberacion)
		return self.estado_acceso == self.EstadoAcceso.ABIERTO

	@property
	def mime_type(self):
		return mimetypes.guess_type(self.archivo.name)[0] or "application/octet-stream"

	def generar_cita_apa(self):
		year = self.fecha_defensa.year if self.fecha_defensa else self.fecha_subida.year
		author = self.autor.get_full_name() or self.autor.email
		return f"{author}. ({year}). {self.titulo} [{self.get_tipo_trabajo_display()}]. {self.url_permanente}."

	def get_absolute_url(self):
		return reverse("repositorio_documentos:detalle", kwargs={"slug": self.url_permanente})
