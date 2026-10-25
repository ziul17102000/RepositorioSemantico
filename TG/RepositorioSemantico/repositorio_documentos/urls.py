from django.urls import path

from . import views

app_name = "repositorio_documentos"
urlpatterns = [
    path("documentos/", views.lista_documentos, name="lista"),
    path("documentos/subir/", views.subir_documento_estudiante, name="subir_estudiante"),
    path("documentos/carga-institucional/", views.subir_documento_institucional, name="subir_institucional"),
    path("documentos/revision/", views.lista_revision, name="revision"),
    path("documentos/<slug:slug>/", views.detalle_documento, name="detalle"),
    path("documentos/<slug:slug>/descargar/", views.descargar_documento, name="descargar"),
    path("documentos/<slug:slug>/editar/", views.editar_documento, name="editar"),
    path("documentos/<slug:slug>/eliminar/", views.eliminar_documento, name="eliminar"),
    path("documentos/revision/<int:pk>/aprobar/", views.aprobar_documento, name="aprobar"),
    path("documentos/revision/<int:pk>/rechazar/", views.rechazar_documento, name="rechazar"),
    path("documentos/avales/", views.lista_avales, name="avales"),
    path("documentos/<int:pk>/avalar/", views.avalar_documento, name="avalar"),
    path("documentos/validacion-academica/", views.lista_validacion_academica, name="validacion"),
    path("documentos/<int:pk>/validar-academicamente/", views.validar_academicamente, name="validar_academicamente"),
]