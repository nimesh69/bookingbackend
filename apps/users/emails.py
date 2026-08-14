from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from rest_framework.exceptions import Throttled  # Or django.core.exceptions.PermissionDenied
from .tokens import reactivation_token
from django.contrib.auth.tokens import default_token_generator

def send_reactivation_email(request, user):
    # 1. Generate a strict Redis key using the user's primary key
    redis_key = f"reactivation_email_lock:{user.pk}"
    
    # 2. Check if this specific user requested an email very recently
    if cache.get(redis_key):
        remaining_time = getattr(cache, 'ttl', lambda k: 60)(redis_key)
        raise Throttled(detail=f"Please wait {remaining_time} seconds before requesting another email.")

    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = reactivation_token.make_token(user)

    link = (
        f"{settings.FRONTEND_URL}/reactivate/"
        f"{uid}/{token}"
    )

    if user.is_deleted:
        subject = 'Cancel your account deletion'
        message = (
            f'Hi {user.username},\n\n'
            f'We received a login attempt on your account which is scheduled for deletion.\n\n'
            f'Click the link below to cancel the deletion and restore your account:\n\n'
            f'{link}\n\n'
            f'This link expires in 30 min.\n\n'
            f'If you do not click this link, your account will be permanently deleted after 30 days.\n\n'
            f'If this wasn\'t you, you can safely ignore this email.'
        )
    else:
        subject = 'Reactivate your account'
        message = (
            f'Hi {user.username},\n\n'
            f'We received a login attempt on your deactivated account.\n\n'
            f'Click the link below to reactivate and sign in:\n\n'
            f'{link}\n\n'
            f'This link expires in 30 min.\n\n'
            f'If this wasn\'t you, you can safely ignore this email.'
        )

    # 3. Fire the email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

    # 4. Set a 60-second cooldown in Redis after a successful send
    cache.set(redis_key, True, timeout=60)



def send_password_reset_email(request, user):
    """Send password reset email with dynamic domain, same as reactivation email."""
    # Generate strict unique redis key
    redis_key = f"resetpassword_email_lock:{user.pk}"
    # check if this specific user requested an email very recently
    if cache.get(redis_key):
        remaining_time = getattr(cache, 'ttl', lambda k: 60)(redis_key)
        raise Throttled(detail=f"Please wait {remaining_time} seconds before requesting another email.")
    
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    link = (
        f"{settings.RESET_PASSWORD_URL}"
        f"{uid}/{token}"
        f"?username={user.username}"
    )

    subject = 'Reset your password'
    message = (
        f'Hi {user.username},\n\n'
        f'We received a request to reset your password.\n\n'
        f'Click the link below to set a new password:\n\n'
        f'{link}\n\n'
        f'This link expires in 30 min.\n\n'
        f'If you did not request this, you can safely ignore this email.'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    
    cache.set(redis_key, True, timeout=60)

    
def send_account_verification_email(request, user):
    # 1. Generate a strict Redis key using the user's primary key
    redis_key = f"verification_email_lock:{user.pk}"
    
    # 2. Check if this specific user requested an email very recently
    if cache.get(redis_key):
        remaining_time = getattr(cache, 'ttl', lambda k: 60)(redis_key)
        raise Throttled(detail=f"Please wait {remaining_time} seconds before requesting another email.")

    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = reactivation_token.make_token(user)

    link = (
        f"{settings.FRONTEND_URL}/verify/"
        f"{uid}/{token}"
    )

    subject = 'Verify your account'
    message = (
        f'Hi {user.username},\n\n'
        f'Thank you for registering an account with us.\n\n'
        f'Click the link below to verify your email address and activate your account:\n\n'
        f'{link}\n\n'
        f'This link expires in 30 min.\n\n'
        f'If you did not request this, you can safely ignore this email.'
    )

    # 3. Fire the email
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )

    # 4. Set a 60-second cooldown in Redis after a successful send
    cache.set(redis_key, True, timeout=60)
