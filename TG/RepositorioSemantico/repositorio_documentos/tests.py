import hashlib
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from repositorio_usuarios.models import RepositorioUser
from .models import Documento


class FlujoDocumentoTests(TestCase):
	def setUp(self):
		self.estudiante = RepositorioUser.objects.create_user(
			email="estudiante@uni.edu", nombre_completo="Estudiante Prueba", cedula="DOC-001",
			password="ClaveSegura2026$Documento", is_active=True, rol="estudiante",
		)
		self.bibliotecario = RepositorioUser.objects.create_user(
			email="biblioteca@uni.edu", nombre_completo="Bibliotecario Prueba", cedula="DOC-002",
			password="ClaveSegura2026$Documento", is_active=True, is_staff=True, rol="bibliotecario",
		)

	def _archivo(self):
		contenido = b"%PDF-1.4 documento academico de prueba"
		return SimpleUploadedFile("trabajo.pdf", contenido, content_type="application/pdf"), contenido

	def _datos(self):
		return {
			"titulo": "Una tesis sobre repositorios",
			"tutor": "Dra. Directora",
			"resumen": "Resumen académico suficientemente descriptivo.",
			"fecha_defensa": "2026-10-20",
			"tipo_trabajo": "tesis",
			"idioma": "es",
			"palabras_clave": "repositorios, preservación, tesis",
			"licencia": "cc_by",
			"estado_acceso": "abierto",
			"acepta_terminos": "on",
			"autorizo_preservacion": "on",
		}

	def test_autodeposito_calcula_hash_y_queda_pendiente(self):
		self.client.force_login(self.estudiante)
		archivo, contenido = self._archivo()
		response = self.client.post(reverse("repositorio_documentos:subir_estudiante"), self._datos() | {"archivo": archivo})

		self.assertEqual(response.status_code, 302)
		documento = Documento.objects.get(titulo="Una tesis sobre repositorios")
		self.assertEqual(documento.autor, self.estudiante)
		self.assertEqual(documento.estado_revision, Documento.EstadoRevision.PENDIENTE)
		self.assertEqual(documento.checksum_sha256, hashlib.sha256(contenido).hexdigest())
		self.assertTrue(documento.es_pdf)
		self.assertFalse(documento.puede_descargar)

	def test_bibliotecario_aprueba_y_documento_aparece_publico(self):
		self.client.force_login(self.estudiante)
		archivo, _ = self._archivo()
		self.client.post(reverse("repositorio_documentos:subir_estudiante"), self._datos() | {"archivo": archivo})
		documento = Documento.objects.get()

		self.client.force_login(self.bibliotecario)
		revision = self.client.get(reverse("repositorio_documentos:revision"))
		self.assertContains(revision, documento.titulo)
		response = self.client.post(reverse("repositorio_documentos:aprobar", args=[documento.pk]))

		self.assertRedirects(response, reverse("repositorio_documentos:revision"))
		documento.refresh_from_db()
		self.assertEqual(documento.estado_revision, Documento.EstadoRevision.APROBADO)
		self.assertTrue(documento.puede_descargar)

		public_list = self.client.get(reverse("repositorio_documentos:lista"))
		self.assertContains(public_list, documento.titulo)
		detail = self.client.get(documento.get_absolute_url())
		self.assertContains(detail, "Integridad SHA-256")

	def test_carga_institucional_queda_aprobada(self):
		self.client.force_login(self.bibliotecario)
		archivo, _ = self._archivo()
		response = self.client.post(reverse("repositorio_documentos:subir_institucional"), {
			"titulo": "Carga institucional",
			"tutor": "Biblioteca",
			"resumen": "Documento publicado por biblioteca.",
			"fecha_defensa": "2026-10-20",
			"tipo_trabajo": "articulo",
			"idioma": "es",
			"palabras_clave": "biblioteca, investigación",
			"licencia": "cc_by",
			"estado_acceso": "abierto",
			"autor": str(self.estudiante.pk),
			"archivo": archivo,
		})

		self.assertEqual(response.status_code, 302)
		documento = Documento.objects.get(titulo="Carga institucional")
		self.assertEqual(documento.estado_revision, Documento.EstadoRevision.APROBADO)
		self.assertEqual(documento.metodo_ingreso, Documento.MetodoIngreso.CARGA_INSTITUCIONAL)

	def test_documento_pendiente_no_es_publico_para_visitante(self):
		self.client.force_login(self.estudiante)
		archivo, _ = self._archivo()
		self.client.post(reverse("repositorio_documentos:subir_estudiante"), self._datos() | {"archivo": archivo})
		documento = Documento.objects.get()
		self.client.logout()

		response = self.client.get(documento.get_absolute_url())
		self.assertEqual(response.status_code, 404)
