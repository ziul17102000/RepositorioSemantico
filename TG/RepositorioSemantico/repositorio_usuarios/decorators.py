from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .rbac import user_in_group


def rol_requerido(roles):
    legacy_groups = {
        "estudiante": "Estudiantes",
        "bibliotecario": "Bibliotecarios",
        "administrador": "Administradores",
        "tutor": "Tutores",
        "coordinador": "Coordinadores",
    }
    allowed_groups = {legacy_groups.get(role, role) for role in roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesión para realizar esta acción.")
                return redirect(f"/repositorio/login/?next={request.path}")
            if not request.user.is_superuser and not any(user_in_group(request.user, group) for group in allowed_groups):
                messages.error(request, "No tienes permiso para acceder a esta sección.")
                return redirect("repositorio_dashboard:inicio")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def grupo_requerido(groups=None, permission=None):
    required_groups = set(groups or [])

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesión para realizar esta acción.")
                return redirect(f"/repositorio/login/?next={request.path}")
            has_group = request.user.is_superuser or any(user_in_group(request.user, group) for group in required_groups)
            has_permission = not permission or request.user.has_perm(permission)
            if not has_group or not has_permission:
                messages.error(request, "No tienes permiso para acceder a esta sección.")
                return redirect("repositorio_dashboard:inicio")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator