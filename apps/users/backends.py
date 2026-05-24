from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class AllowInactiveBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password):
            return user  # returns even if is_active=False
        return None

    def user_can_authenticate(self, user):
        return True
    



# # apps/users/backends.py

# from django.contrib.auth.backends import ModelBackend
# from django.contrib.auth import get_user_model

# User = get_user_model()

# class EmailOrUsernameBackend(ModelBackend):
#     def authenticate(self, request, username=None, password=None, **kwargs):
#         try:
#             user = User.objects.get(email=username)
#         except User.DoesNotExist:
#             try:
#                 user = User.objects.get(username=username)
#             except User.DoesNotExist:
#                 return None

#         if user.check_password(password) and self.user_can_authenticate(user):
#             return user
#         return None