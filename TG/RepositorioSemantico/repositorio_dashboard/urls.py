from django.urls import path

from . import views

app_name = "repositorio_dashboard"
urlpatterns = [
    path("", views.dashboard_redirect, name="inicio"),
    path("panel/administrador/", views.dashboard_admin, name="admin"),
    path("panel/bibliotecario/", views.dashboard_bibliotecario, name="bibliotecario"),
    path("panel/estudiante/", views.dashboard_estudiante, name="estudiante"),
]