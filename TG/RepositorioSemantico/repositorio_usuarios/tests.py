from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import RepositorioUser
from .rbac import GROUP_ADMINS, GROUP_STUDENTS, ensure_group


class RegistroYAccesoTests(TestCase):
	def test_registro_crea_estudiante_inactivo_y_login_informa_pendiente(self):
		response = self.client.post(reverse("repositorio_usuarios:registro"), {
			"nombre_completo": "Ana Torres",
			"email": "ana@example.edu",
			"cedula": "1234567890",
			"password": "PiedraLimon2026$Oceano",
			"confirmacion": "PiedraLimon2026$Oceano",
			"acepta_terminos": "on",
		}, follow=True)

		estudiante = RepositorioUser.objects.get(email="ana@example.edu")
		self.assertFalse(estudiante.is_active)
		self.assertTrue(estudiante.groups.filter(name=GROUP_STUDENTS).exists())
		self.assertContains(response, "Tu cuenta está pendiente de aprobación.")

		response = self.client.post(reverse("repositorio_usuarios:login"), {
			"email": estudiante.email,
			"password": "PiedraLimon2026$Oceano",
		})
		self.assertContains(response, "Tu cuenta está pendiente de aprobación.")
		self.assertFalse(response.wsgi_request.user.is_authenticated)

	def test_registro_requiere_aceptar_terminos(self):
		response = self.client.post(reverse("repositorio_usuarios:registro"), {
			"nombre_completo": "Ana Torres",
			"email": "ana@example.edu",
			"cedula": "1234567890",
			"password": "PiedraLimon2026$Oceano",
			"confirmacion": "PiedraLimon2026$Oceano",
		})

		self.assertEqual(response.status_code, 200)
		self.assertFalse(RepositorioUser.objects.exists())


class AprobacionTests(TestCase):
	def setUp(self):
		self.administrador = RepositorioUser.objects.create_superuser(
			email="admin@example.edu",
			nombre_completo="Admin Principal",
			cedula="000000001",
			password="PiedraLimon2026$Oceano",
		)
		self.estudiante = RepositorioUser.objects.create_user(
			email="estudiante@example.edu",
			nombre_completo="Estudiante Prueba",
			cedula="000000002",
			password="PiedraLimon2026$Oceano",
		)
		self.estudiante.groups.add(ensure_group(GROUP_STUDENTS))

	def test_administrador_aprueba_y_queda_registrado(self):
		self.client.force_login(self.administrador)
		response = self.client.post(reverse("repositorio_usuarios:aprobar", args=[self.estudiante.pk]))

		self.assertRedirects(response, reverse("repositorio_usuarios:pendientes"))
		self.estudiante.refresh_from_db()
		self.assertTrue(self.estudiante.is_active)
		self.assertEqual(self.estudiante.aprobado_por, self.administrador)
		self.assertIsNotNone(self.estudiante.fecha_aprobacion)

		response = self.client.post(reverse("repositorio_usuarios:login"), {
			"email": self.estudiante.email,
			"password": "PiedraLimon2026$Oceano",
		})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse("repositorio_dashboard:inicio"))

	@patch("repositorio_usuarios.management.commands.crear_admin.getpass", side_effect=["FuerteClave2026$Rio", "FuerteClave2026$Rio"])
	@patch("builtins.input", side_effect=["nuevo-admin@example.edu", "Nuevo Admin", "000000003"])
	def test_comando_crea_superusuario_administrador(self, mocked_input, mocked_getpass):
		output = StringIO()
		call_command("crear_admin", stdout=output)

		admin_user = RepositorioUser.objects.get(email="nuevo-admin@example.edu")
		self.assertTrue(admin_user.is_active)
		self.assertTrue(admin_user.is_staff)
		self.assertTrue(admin_user.is_superuser)
		self.assertTrue(admin_user.groups.filter(name=GROUP_ADMINS).exists())
		self.assertIn("creado correctamente", output.getvalue())

	@patch.dict("os.environ", {"DJANGO_SUPERUSER_PASSWORD": "FuerteClave2026$Rio"})
	def test_createsuperuser_estandar_crea_admin_con_cedula(self):
		call_command(
			"createsuperuser",
			email="estandar-admin@example.edu",
			interactive=False,
			stdout=StringIO(),
		)

		admin_user = RepositorioUser.objects.get(email="estandar-admin@example.edu")
		self.assertIsNone(admin_user.cedula)
		self.assertEqual(admin_user.nombre_completo, "")
		self.assertTrue(admin_user.groups.filter(name=GROUP_ADMINS).exists())
		self.assertTrue(admin_user.is_active)
		self.assertTrue(admin_user.is_staff)
		self.assertTrue(admin_user.is_superuser)

	def test_estudiante_no_puede_ver_pendientes(self):
		self.estudiante.is_active = True
		self.estudiante.save(update_fields=["is_active"])
		self.client.force_login(self.estudiante)

		response = self.client.get(reverse("repositorio_usuarios:pendientes"))

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response.url, reverse("repositorio_dashboard:inicio"))

	def test_raiz_sin_sesion_lleva_al_login(self):
		response = self.client.get(reverse("repositorio_dashboard:inicio"))
		login_url = reverse("repositorio_usuarios:login")
		self.assertRedirects(response, f"{login_url}?next={reverse('repositorio_dashboard:inicio')}")

	def test_dashboard_admin_y_admin_django_renderizan(self):
		self.client.force_login(self.administrador)

		dashboard = self.client.get(reverse("repositorio_dashboard:admin"))
		admin_users = self.client.get("/admin/repositorio_usuarios/repositoriouser/")
		admin_add_user = self.client.get("/admin/repositorio_usuarios/repositoriouser/add/")
		create_librarian = self.client.get(reverse("repositorio_usuarios:crear_bibliotecario"))
		edit_config = self.client.get(reverse("repositorio_config:editar"))
		pending_students = self.client.get(reverse("repositorio_usuarios:pendientes"))

		self.assertEqual(dashboard.status_code, 200)
		self.assertContains(dashboard, "Usuarios totales")
		self.assertEqual(admin_users.status_code, 200)
		self.assertEqual(admin_add_user.status_code, 200)
		self.assertEqual(create_librarian.content.count(b"<form"), 2)
		self.assertEqual(edit_config.content.count(b"<form"), 2)
		self.assertContains(pending_students, "rejectModal")
