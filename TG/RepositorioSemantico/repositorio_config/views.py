from django.contrib import messages
from django.shortcuts import redirect, render

from repositorio_usuarios.decorators import rol_requerido
from .forms import ConfiguracionForm
from .models import Configuracion


@rol_requerido(["administrador"])
def editar_configuracion(request):
	configuracion = Configuracion.get_solo()
	form = ConfiguracionForm(request.POST or None, request.FILES or None, instance=configuracion)
	if request.method == "POST" and form.is_valid():
		form.save()
		messages.success(request, "La configuración institucional fue actualizada.")
		return redirect("repositorio_config:editar")
	return render(request, "repositorio_config/editar_configuracion.html", {"form": form})
