from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
def verify_owner_password_or_403(request, owner):
    password = request.data.get('password')
    if not password:
        raise ValidationError({'password': 'Password is required.'})
    if not request.user.check_password(password):
        raise ValidationError({'password': 'Incorrect password.'})
    if owner != request.user:
        raise PermissionDenied("You don't own this resource.")