# RepositorioSemantico

Fase 1 de un repositorio académico Django con registro de estudiantes, aprobación por bibliotecario/administrador y dashboards por rol.

## Entorno

El entorno virtual está en `TG/.venv` y las dependencias están en `TG/RepositorioSemantico/requirements.txt`.

Desde la carpeta `TG`:

```bash
source .venv/bin/activate
cd RepositorioSemantico
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

`createsuperuser` solicita solamente correo y contraseña, como el comando estándar de Django. El nombre completo y la cédula se pueden completar luego desde el admin si los necesitas. También puedes usar `python manage.py crear_admin`, que ofrece el mismo rol con una confirmación adicional de la contraseña. Abre `/` o `/repositorio/` en el navegador del Codespace e inicia sesión con el correo y la contraseña creados. Después, crea un bibliotecario desde **Usuarios**.

## Probar el flujo

1. Crea el administrador con `python manage.py createsuperuser`.
2. Inicia sesión en `/repositorio/login/` y crea un bibliotecario.
3. Cierra la sesión e inscribe un estudiante en `/repositorio/registro/`.
4. Inicia sesión como administrador o bibliotecario, abre **Pendientes** y aprueba o rechaza la solicitud.
5. El estudiante aprobado ya puede iniciar sesión y verá su panel.

## Migraciones y pruebas

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
```

## PDF.js local

El visor PDF utiliza PDF.js local en `repositorio_documentos/static/pdfjs/`. Para instalar o actualizarlo, descarga la distribución oficial desde [mozilla/pdf.js releases](https://github.com/mozilla/pdf.js/releases), el archivo `pdfjs-<version>-dist.zip`, y copia el contenido completo del ZIP dentro de esa carpeta. Deben existir, como mínimo, `static/pdfjs/web/viewer.html`, `static/pdfjs/build/pdf.mjs` y `static/pdfjs/build/pdf.worker.mjs`. No cambies la estructura interna de `web/` ni `build/`.

La versión instalada para esta fase es PDF.js 4.10.38. En desarrollo Django sirve estos archivos automáticamente con `DEBUG=1`; en producción ejecuta `python manage.py collectstatic` y configura el servidor web para servir `STATIC_ROOT`.

## Flujo de documentos

1. Ejecuta migraciones con `python manage.py migrate`.
2. Crea o usa un estudiante activo y entra a `/repositorio/documentos/subir/` para enviar un PDF, DOCX o imagen.
3. Entra como bibliotecario o administrador a `/repositorio/documentos/revision/` y aprueba el autodepósito.
4. El trabajo aparecerá en `/repositorio/documentos/`; su detalle muestra Dublin Core, licencia, cita APA y SHA-256.
5. Para reparar documentos antiguos sin hash ejecuta `python manage.py recalcular_hashes`. Añade `--todos` para recalcular también los hashes existentes.

SQLite está configurado para desarrollo. En producción configura `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS` y la conexión a PostgreSQL antes de publicar.