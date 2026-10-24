from django.urls import path

from . import views

app_name = "repositorio_usuarios"
urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("registro/", views.registro_estudiante, name="registro"),
    path("pendientes/", views.lista_estudiantes_pendientes, name="pendientes"),
    path("aprobar/<int:pk>/", views.aprobar_estudiante, name="aprobar"),
    path("rechazar/<int:pk>/", views.rechazar_estudiante, name="rechazar"),
    path("usuarios/", views.lista_usuarios, name="usuarios"),
    path("crear-bibliotecario/", views.crear_bibliotecario, name="crear_bibliotecario"),
]