# auth/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Try cookie first, fall back to Authorization header
        raw_token = request.COOKIES.get('access_token')
        if raw_token is None:
            return super().authenticate(request)   # header fallback (WebSocket, mobile, etc.)
        try:
            validated = self.get_validated_token(raw_token)
            return self.get_user(validated), validated
        except (InvalidToken, TokenError):
            return None