# nirit/auth.py
"""
Authentication Backend.

"""
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """
    Authenticate against django.contrib.auth.models.User using
    e-mail address instead of username.

    """
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(email__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
