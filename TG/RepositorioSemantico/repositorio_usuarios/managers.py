from django.contrib.auth.base_user import BaseUserManager


class RepositorioUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, nombre_completo="", cedula="", password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        nombre_completo = (nombre_completo or "").strip()
        cedula = (cedula or "").strip() or None
        user = self.model(
            email=self.normalize_email(email).strip().lower(),
            nombre_completo=nombre_completo,
            cedula=cedula,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre_completo="", cedula="", password=None, **extra_fields):
        extra_fields.setdefault("rol", "administrador")
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True e is_superuser=True.")
        return self.create_user(email, nombre_completo, cedula, password, **extra_fields)