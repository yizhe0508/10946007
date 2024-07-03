from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

class EmailOrUsernameModelBackend(BaseBackend):
    def authenticate(self, request, username_or_email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            if '@' in username_or_email:
                user = UserModel.objects.get(email=username_or_email)
            else:
                user = UserModel.objects.get(username=username_or_email)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
