from django.core.management.base import BaseCommand

from repositorio_documentos.models import Documento


class Command(BaseCommand):
    help = "Recalcula el SHA-256 de documentos que no tienen hash o de todos si se usa --todos."

    def add_arguments(self, parser):
        parser.add_argument("--todos", action="store_true", help="Recalcula también hashes existentes.")

    def handle(self, *args, **options):
        queryset = Documento.objects.exclude(archivo="")
        if not options["todos"]:
            queryset = queryset.filter(checksum_sha256="")
        count = 0
        for documento in queryset.iterator():
            documento.checksum_sha256 = ""
            documento.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Hashes recalculados: {count}."))