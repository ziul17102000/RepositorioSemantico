from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper

from .models import Documento


class DocumentoBaseForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ["titulo", "tutor", "resumen", "fecha_defensa", "tipo_trabajo", "idioma", "palabras_clave", "archivo", "licencia", "estado_acceso", "fecha_liberacion"]
        labels = {"titulo": "Título", "tutor": "Tutor o director", "resumen": "Resumen", "fecha_defensa": "Fecha de defensa", "tipo_trabajo": "Tipo de trabajo", "idioma": "Idioma", "palabras_clave": "Palabras clave", "archivo": "Archivo digital", "licencia": "Licencia Creative Commons", "estado_acceso": "Acceso del documento", "fecha_liberacion": "Fecha de liberación del embargo"}
        widgets = {"resumen": forms.Textarea(attrs={"rows": 5}), "fecha_defensa": forms.DateInput(attrs={"type": "date"}), "fecha_liberacion": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean_archivo(self):
        archivo = self.cleaned_data.get("archivo")
        if archivo and archivo.size > 50 * 1024 * 1024:
            raise ValidationError("El archivo no puede superar los 50 MB.")
        return archivo


class DocumentoEstudianteForm(DocumentoBaseForm):
    acepta_terminos = forms.BooleanField(label="Acepto la licencia seleccionada y autorizo la preservación digital de este trabajo.", required=True)
    autorizo_preservacion = forms.BooleanField(label="Autorizo la preservación digital y el acceso según la configuración elegida.", required=True)

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
    autor = forms.ModelChoiceField(queryset=get_user_model().objects.filter(rol="estudiante", is_active=True), label="Autor del trabajo", required=False)

    def save(self, commit=True):
        documento = super().save(commit=False)
        documento.metodo_ingreso = Documento.MetodoIngreso.CARGA_INSTITUCIONAL
        documento.estado_revision = Documento.EstadoRevision.APROBADO
        documento.acepto_terminos = True
        documento.autorizo_preservacion = True
        if commit:
            documento.save()
        return documento