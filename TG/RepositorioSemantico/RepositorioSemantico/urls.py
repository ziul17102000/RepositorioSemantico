"""
URL configuration for RepositorioSemantico project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
	path("", RedirectView.as_view(pattern_name="repositorio_usuarios:login", permanent=False)),
    path("admin/", admin.site.urls),
    path("repositorio/", include("repositorio_usuarios.urls")),
    path("repositorio/", include("repositorio_dashboard.urls")),
    path("repositorio/", include("repositorio_documentos.urls")),
    path("repositorio/configuracion/", include("repositorio_config.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
