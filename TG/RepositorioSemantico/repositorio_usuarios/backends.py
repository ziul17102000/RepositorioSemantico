from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class RepositorioUserBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        login_email = email or username or kwargs.get("email")
        if not login_email or password is None:
            return None
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email__iexact=login_email.strip())
        except user_model.DoesNotExist:
            user_model().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None