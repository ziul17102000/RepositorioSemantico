from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def rol_requerido(roles):
    allowed_roles = set(roles)

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.rol not in allowed_roles:
                messages.error(request, "No tienes permiso para acceder a esta sección.")
                return redirect("repositorio_dashboard:inicio")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator