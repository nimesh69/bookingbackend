# auth/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            # Only fall back to header if Authorization header actually exists
            if request.headers.get('Authorization'):
                return super().authenticate(request)
            return None  # No cookie, no header → anonymous
        
        try:
            validated = self.get_validated_token(raw_token)
            return self.get_user(validated), validated
        except (InvalidToken, TokenError):
            return None