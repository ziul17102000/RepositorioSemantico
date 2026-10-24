from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from repositorio_usuarios.models import RepositorioUser


class Command(BaseCommand):
    help = "Crea el primer administrador del RepositorioSemantico."

    def handle(self, *args, **options):
        email = input("Correo electrónico: ").strip().lower()
        nombre = input("Nombre completo: ").strip()
        cedula = input("Cédula: ").strip()
        password = getpass("Contraseña: ")
        if password != getpass("Confirma la contraseña: "):
            raise CommandError("Las contraseñas no coinciden.")
        if RepositorioUser.objects.filter(email__iexact=email).exists():
            raise CommandError("Ya existe una cuenta con ese correo.")
        if RepositorioUser.objects.filter(cedula=cedula).exists():
            raise CommandError("Ya existe una cuenta con esa cédula.")
        try:
            admin_user = RepositorioUser.objects.create_superuser(email=email, nombre_completo=nombre, cedula=cedula, password=password)
        except (TypeError, ValueError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(self.style.SUCCESS(f"Administrador {admin_user.email} creado correctamente."))