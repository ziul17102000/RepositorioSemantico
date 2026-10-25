from django.core.validators import RegexValidator
from django.db import models


hex_color_validator = RegexValidator(regex=r"^#[0-9A-Fa-f]{6}$", message="Introduce un color hexadecimal válido, por ejemplo #16845B.")


class Configuracion(models.Model):
	nombre_universidad = models.CharField(max_length=180, default="Universidad")
	siglas = models.CharField(max_length=24, default="UNI")
	logo = models.ImageField(upload_to="configuracion/", blank=True, null=True)
	color_primario = models.CharField(max_length=7, default="#16845B", validators=[hex_color_validator])
	color_secundario = models.CharField(max_length=7, default="#123D34", validators=[hex_color_validator])
	correo_contacto = models.EmailField(blank=True)
	texto_terminos = models.TextField(blank=True, default="Al registrarme confirmo que los datos proporcionados son correctos.")
	permitir_registro_estudiantes = models.BooleanField(default=True)
	licencias_habilitadas = models.ManyToManyField("Licencia", blank=True, related_name="configuraciones")

	class Meta:
		verbose_name = "configuración institucional"
		verbose_name_plural = "configuración institucional"

	def __str__(self):
		return self.nombre_universidad

	def save(self, *args, **kwargs):
		self.pk = 1
		super().save(*args, **kwargs)

	def delete(self, *args, **kwargs):
		return None

	@classmethod
	def get_solo(cls):
		configuracion, _ = cls.objects.get_or_create(pk=1)
		return configuracion


class Licencia(models.Model):
	CODIGOS = (
		("cc0", "CC0 1.0 Universal"),
		("cc_by", "CC BY 4.0"),
		("cc_by_sa", "CC BY-SA 4.0"),
		("cc_by_nc", "CC BY-NC 4.0"),
		("cc_by_nc_sa", "CC BY-NC-SA 4.0"),
		("cc_by_nd", "CC BY-ND 4.0"),
		("cc_by_nc_nd", "CC BY-NC-ND 4.0"),
	)
	codigo = models.CharField(max_length=20, unique=True)
	nombre = models.CharField(max_length=100)
	descripcion = models.TextField()
	url_logo = models.URLField(blank=True)
	activa = models.BooleanField(default=True)

	class Meta:
		ordering = ["codigo"]
		verbose_name = "licencia"
		verbose_name_plural = "licencias"

	def __str__(self):
		return self.nombre

	@property
	def logo_local(self):
		return f"repositorio/img/cc/{self.codigo}.png"

	@property
	def url_terminos(self):
		return self.url_logo or f"https://creativecommons.org/licenses/{self.codigo.replace('_', '-')}/4.0/"

	@classmethod
	def crear_predeterminadas(cls):
		textos = {
			"cc0": "Dominio público. Permite cualquier uso sin exigir condiciones.",
			"cc_by": "Permite compartir y adaptar, incluso comercialmente, dando crédito.",
			"cc_by_sa": "Permite adaptar y compartir, incluso comercialmente, con la misma licencia.",
			"cc_by_nc": "Permite compartir y adaptar solo para usos no comerciales, dando crédito.",
			"cc_by_nc_sa": "Uso no comercial y las adaptaciones deben conservar la misma licencia.",
			"cc_by_nd": "Permite compartir, pero no modificar el trabajo. Requiere atribución.",
			"cc_by_nc_nd": "Solo compartir sin modificar y sin uso comercial. Requiere atribución.",
		}
		for codigo, nombre in cls.CODIGOS:
			cls.objects.get_or_create(codigo=codigo, defaults={"nombre": nombre, "descripcion": textos[codigo]})
