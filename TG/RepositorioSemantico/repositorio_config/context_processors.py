from .models import Configuracion


def config_repositorio(request):
    return {"config_repositorio": Configuracion.objects.first()}