from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from repositorio_usuarios.rbac import GROUP_PERMISSIONS, INITIAL_GROUPS


class Command(BaseCommand):
    help = "Crea los grupos RBAC iniciales y les asigna sus permisos."

    def handle(self, *args, **options):
        for group_name in INITIAL_GROUPS:
            Group.objects.get_or_create(name=group_name)
        for group_name, permission_names in GROUP_PERMISSIONS.items():
            group = Group.objects.get(name=group_name)
            for permission_name in permission_names:
                app_label, codename = permission_name.split(".", 1)
                permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                group.permissions.add(permission)
        self.stdout.write(self.style.SUCCESS("Grupos RBAC y permisos iniciales creados correctamente."))