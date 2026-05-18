# auth/utils.py
from django.conf import settings

# auth/utils.py
def set_auth_cookies(response, tokens):
    secure = not settings.DEBUG  # True in production, False in dev
    samesite = getattr(settings, 'SESSION_COOKIE_SAMESITE', 'Lax')

    response.set_cookie(
        key='access_token',
        value=tokens['access'],
        max_age=settings.ACCESS_TOKEN_LIFETIME_SECONDS,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path='/',
    )
    response.set_cookie(
        key='refresh_token',
        value=tokens['refresh'],
        max_age=settings.REFRESH_TOKEN_LIFETIME_SECONDS,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path='/',           # <-- FIX: was '/api/auth/'
    )


def clear_auth_cookies(response):
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')  # <-- MATCH