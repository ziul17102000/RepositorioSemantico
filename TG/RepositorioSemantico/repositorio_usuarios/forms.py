from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper

from .models import RepositorioUser


class LoginForm(forms.Form):
    email = forms.EmailField(label="Correo electrónico", widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "form-control"}))
    password = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": "form-control"}))


class RegistroEstudianteForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    confirmacion = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    acepta_terminos = forms.BooleanField(label="Acepto los términos y condiciones")

    class Meta:
        model = RepositorioUser
        fields = ["nombre_completo", "email", "cedula"]
        labels = {"nombre_completo": "Nombre completo", "email": "Correo electrónico", "cedula": "Cédula"}
        widgets = {"nombre_completo": forms.TextInput(attrs={"autocomplete": "name"}), "email": forms.EmailInput(attrs={"autocomplete": "email"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre_completo"].required = True
        self.fields["cedula"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if RepositorioUser.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data["cedula"].strip()
        if RepositorioUser.objects.filter(cedula=cedula).exists():
            raise ValidationError("Ya existe una cuenta con esta cédula.")
        return cedula

    def clean(self):
        cleaned_data = super().clean()
        password, confirmation = cleaned_data.get("password"), cleaned_data.get("confirmacion")
        if password and confirmation and password != confirmation:
            self.add_error("confirmacion", "Las contraseñas no coinciden.")
        if password:
            candidate = RepositorioUser(email=cleaned_data.get("email", ""), nombre_completo=cleaned_data.get("nombre_completo", ""), cedula=cleaned_data.get("cedula", ""))
            try:
                validate_password(password, candidate)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = RepositorioUser.Roles.ESTUDIANTE
        user.is_active = False
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CrearBibliotecarioForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    confirmacion = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    class Meta:
        model = RepositorioUser
        fields = ["nombre_completo", "email", "cedula"]
        labels = {"nombre_completo": "Nombre completo", "email": "Correo electrónico", "cedula": "Cédula"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nombre_completo"].required = True
        self.fields["cedula"].required = True
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        password, confirmation = cleaned_data.get("password"), cleaned_data.get("confirmacion")
        if password and password != confirmation:
            self.add_error("confirmacion", "Las contraseñas no coinciden.")
        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol, user.is_active, user.is_staff = RepositorioUser.Roles.BIBLIOTECARIO, True, False
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user