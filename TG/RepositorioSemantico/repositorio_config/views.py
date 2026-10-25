from django.contrib import messages
from django.shortcuts import redirect, render

from repositorio_usuarios.decorators import rol_requerido
from repositorio_usuarios.rbac import audit
from .forms import ConfiguracionForm
from .models import Configuracion


@rol_requerido(["administrador"])
def editar_configuracion(request):
	configuracion = Configuracion.get_solo()
	form = ConfiguracionForm(request.POST or None, request.FILES or None, instance=configuracion)
	if request.method == "POST" and form.is_valid():
		form.save()
		if not configuracion.licencias_habilitadas.filter(activa=True).exists():
			messages.warning(request, "No había licencias activas; se dejó CC BY-NC-ND como opción predeterminada.")
		audit(request.user, "cambiar_licencia", request, "Actualizó las licencias habilitadas")
		messages.success(request, "La configuración institucional fue actualizada.")
		return redirect("repositorio_config:editar")
	return render(request, "repositorio_config/editar_configuracion.html", {"form": form})
