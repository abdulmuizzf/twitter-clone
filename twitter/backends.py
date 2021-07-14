from django.contrib.auth.backends import ModelBackend

from .models import User

class SawoBackend(ModelBackend):
    def authenticate(self, request, username, password=None, token=None):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        else:
            # Sawo Auth goes here
            pass
        return user
    
    def get_user(self, username):
        try:
            return User.objects.get(pk=username)
        except User.DoesNotExist:
            return None