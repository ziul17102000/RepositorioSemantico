from django import forms
from crispy_forms.helper import FormHelper

from .models import Configuracion


class ConfiguracionForm(forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = ["nombre_universidad", "siglas", "logo", "color_primario", "color_secundario", "correo_contacto", "texto_terminos", "permitir_registro_estudiantes"]
        labels = {
            "nombre_universidad": "Nombre de la universidad", "siglas": "Siglas", "logo": "Logo institucional",
            "color_primario": "Color primario", "color_secundario": "Color secundario", "correo_contacto": "Correo de contacto",
            "texto_terminos": "Términos y condiciones", "permitir_registro_estudiantes": "Permitir registro de estudiantes",
        }
        widgets = {"texto_terminos": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False