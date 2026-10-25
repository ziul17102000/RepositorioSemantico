from .rbac import GROUP_ADMINS, GROUP_LIBRARIANS, GROUP_STUDENTS, group_names


def rbac_context(request):
    groups = group_names(request.user)
    return {
        "user_groups": groups,
        "es_administrador": request.user.is_superuser or GROUP_ADMINS in groups,
        "es_bibliotecario": request.user.is_superuser or GROUP_LIBRARIANS in groups,
        "es_estudiante": GROUP_STUDENTS in groups,
    }