from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.conf import settings
from .tokens import reactivation_token
from django.contrib.auth.tokens import default_token_generator

def send_reactivation_email(request, user):
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
            f'This link expires in 1 hour.\n\n'
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
            f'This link expires in 1 hour.\n\n'
            f'If this wasn\'t you, you can safely ignore this email.'
        )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(request, user):
    """Send password reset email with dynamic domain, same as reactivation email."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    link = (
        f"{settings.FRONTEND_URL}/reset-password/"
        f"{uid}/{token}"
        f"?username={user.username}"
    )

    subject = 'Reset your password'
    message = (
        f'Hi {user.username},\n\n'
        f'We received a request to reset your password.\n\n'
        f'Click the link below to set a new password:\n\n'
        f'{link}\n\n'
        f'This link expires in 1 hour.\n\n'
        f'If you did not request this, you can safely ignore this email.'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )