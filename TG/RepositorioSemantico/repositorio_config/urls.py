from django.urls import path

from . import views

app_name = "repositorio_config"
urlpatterns = [path("", views.editar_configuracion, name="editar")]