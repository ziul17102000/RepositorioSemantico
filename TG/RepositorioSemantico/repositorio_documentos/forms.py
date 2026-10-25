from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper

from repositorio_config.models import Configuracion, Licencia
from repositorio_usuarios.rbac import GROUP_STUDENTS, GROUP_TUTORS
from .models import Documento


class DocumentoBaseForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ["titulo", "tutor", "resumen", "fecha_defensa", "tipo_trabajo", "idioma", "palabras_clave", "archivo", "portada", "licencia", "estado_acceso", "fecha_liberacion"]
        labels = {"titulo": "Título", "tutor": "Tutor o director", "resumen": "Resumen", "fecha_defensa": "Fecha de defensa", "tipo_trabajo": "Tipo de trabajo", "idioma": "Idioma del documento", "palabras_clave": "Palabras clave", "archivo": "Archivo PDF", "portada": "Portada (opcional)", "licencia": "Licencia Creative Commons", "estado_acceso": "Disponibilidad del documento", "fecha_liberacion": "Fecha en que termina la restricción"}
        help_texts = {"archivo": "Solo PDF. Tamaño máximo: 50 MB.", "estado_acceso": "Abierto: cualquiera puede leerlo. Embargado: se publicará después de la fecha indicada. Restringido: no se descarga públicamente.", "fecha_liberacion": "Solo completa este campo si eliges Embargado."}
        widgets = {"resumen": forms.Textarea(attrs={"rows": 5}), "fecha_defensa": forms.DateInput(attrs={"type": "date"}), "fecha_liberacion": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["archivo"].widget.attrs["accept"] = ".pdf,application/pdf"
        self.fields["archivo"].help_text = "Solo PDF. Tamaño máximo: 50 MB."
        self.fields["estado_acceso"].help_text = "Abierto: disponible tras aprobación. Embargado: se libera en una fecha. Restringido: sin descarga pública."
        self.fields["fecha_liberacion"].help_text = "Solo se usa cuando eliges Embargado."
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if archivo and archivo.size > 50 * 1024 * 1024:
            raise ValidationError("El archivo no puede superar los 50 MB.")
        return archivo

    def clean(self):
        cleaned_data = super().clean()
        access = cleaned_data.get("estado_acceso")
        release_date = cleaned_data.get("fecha_liberacion")
        if access == Documento.EstadoAcceso.EMBARGADO and not release_date:
            self.add_error("fecha_liberacion", "Indica la fecha en que el documento quedará disponible.")
        if access != Documento.EstadoAcceso.EMBARGADO:
            cleaned_data["fecha_liberacion"] = None
        return cleaned_data


class DocumentoEstudianteForm(DocumentoBaseForm):
    acepta_terminos = forms.BooleanField(label="Acepto la licencia seleccionada y autorizo la preservación digital de este trabajo.", required=True)
    autorizo_preservacion = forms.BooleanField(label="Autorizo la preservación digital y el acceso según la configuración elegida.", required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["licencia"].widget = forms.RadioSelect()
        Licencia.crear_predeterminadas()
        configuracion = Configuracion.get_solo()
        activas = configuracion.licencias_habilitadas.filter(activa=True)
        if not activas.exists():
            activas = Licencia.objects.filter(codigo="cc_by_nc_nd", activa=True)
        self.fields["licencia"].choices = [(licencia.codigo, licencia.nombre) for licencia in activas]
        self.license_options = list(activas.values("codigo", "nombre", "descripcion"))

    def clean_licencia(self):
        licencia = self.cleaned_data["licencia"]
        configuracion = Configuracion.get_solo()
        activas = configuracion.licencias_habilitadas.filter(activa=True)
        if not activas.exists():
            activas = Licencia.objects.filter(codigo="cc_by_nc_nd", activa=True)
        if not activas.filter(codigo=licencia).exists():
            raise ValidationError("La licencia seleccionada no está habilitada actualmente.")
        return licencia

    def save(self, commit=True):
        documento = super().save(commit=False)
        documento.metodo_ingreso = Documento.MetodoIngreso.AUTODEPOSITO
        documento.estado_revision = Documento.EstadoRevision.PENDIENTE
        documento.acepto_terminos = self.cleaned_data["acepta_terminos"]
        documento.autorizo_preservacion = self.cleaned_data["autorizo_preservacion"]
        if commit:
            documento.save()
        return documento


class DocumentoInstitucionalForm(DocumentoBaseForm):
    autor = forms.ModelChoiceField(queryset=get_user_model().objects.filter(groups__name=GROUP_STUDENTS, is_active=True).distinct(), label="Autor del trabajo", required=False)
    tutor_asignado = forms.ModelChoiceField(queryset=get_user_model().objects.filter(groups__name=GROUP_TUTORS, is_active=True).distinct(), label="Tutor asignado", required=False)

    def save(self, commit=True):
        documento = super().save(commit=False)
        documento.metodo_ingreso = Documento.MetodoIngreso.CARGA_INSTITUCIONAL
        documento.estado_revision = Documento.EstadoRevision.APROBADO
        documento.acepto_terminos = True
        documento.autorizo_preservacion = True
        if commit:
            documento.save()
        return documento