from django.contrib.auth import authenticate, get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils import timezone
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiTypes, inline_serializer
from rest_framework import serializers as drf_serializers
from .utils import set_auth_cookies, clear_auth_cookies
from .serializer import (
    LoginRequestSerializer, LoginResponseSerializer,
    SignupRequestSerializer, SignupResponseSerializer,
    PasswordResetRequestSerializer, PasswordResetResponseSerializer,
    PasswordResetConfirmRequestSerializer, PasswordResetConfirmResponseSerializer,
    DeactivateAccountRequestSerializer, SuccessResponseSerializer,
    DeleteAccountRequestSerializer,
    LogoutRequestSerializer, TokenRefreshResponseSerializer,
    MeResponseSerializer, WsTicketResponseSerializer,
    ReactivateResponseSerializer, UserDetailSerializer,
    InactiveAccountResponseSerializer, ErrorResponseSerializer
)
import json
import secrets
from django.core.cache import cache
from .forms import SignUpForm, CustomPasswordResetForm
from .tokens import reactivation_token
from .emails import send_reactivation_email, send_password_reset_email
from .backends import AllowInactiveBackend

User = get_user_model()


def get_tokens_for_user(user):
    """Generate JWT access + refresh token pair for a user."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class WsTicketView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='ws_ticket',
        tags=['Auth'],
        responses=WsTicketResponseSerializer
    )
    def get(self, request):
        # Generate a short-lived single-use ticket
        ticket = secrets.token_urlsafe(32)
        # Store in cache: ticket → user_id, expires in 30 seconds
        cache.set(f'ws_ticket:{ticket}', request.user.id, timeout=30)
        return Response({'ticket': ticket})


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id='login',
        tags=['Auth'],
        request=LoginRequestSerializer,
        responses={
            200: LoginResponseSerializer,
            401: ErrorResponseSerializer,
            403: InactiveAccountResponseSerializer,
        }
    )
    def post(self, request):
        serializer = LoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data.get('username')
        password = serializer.validated_data.get('password')

        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active or getattr(user, 'is_deleted', False):
            send_reactivation_email(request, user)
            return Response({
                'error': 'account_inactive',
                'message': 'Account is inactive. Reactivation email sent.',
            }, status=status.HTTP_403_FORBIDDEN)

        tokens = get_tokens_for_user(user)
        user_data = {
            'user': {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'username': user.username,
                'email': user.email,
                'phone': getattr(user, 'phone', None),
                'avatar': user.avatar.url if user.avatar else None,
                'role': user.role,
                'createdAt': user.date_joined.isoformat(),
            }
        }
        is_mobile = request.headers.get('X-Client-Type') == 'mobile'
        if is_mobile:
            return Response({
                **user_data,
                'access': tokens['access'],
                'refresh': tokens['refresh'],
            }, status=status.HTTP_200_OK)
        else:
            response = Response(user_data, status=status.HTTP_200_OK)
            set_auth_cookies(response, tokens)
            return response


class LogoutView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        operation_id='logout',
        tags=['Auth'],
        request=LogoutRequestSerializer,
        responses=SuccessResponseSerializer
    )
    def post(self, request):
        is_mobile = request.headers.get('X-Client-Type') == 'mobile'

        # ─── MOBILE FLOW ─────────────────────────────
        if is_mobile:
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return Response(
                    {'error': 'Refresh token required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                return Response(
                    {'error': 'Invalid or expired token'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {'success': True},
                status=status.HTTP_200_OK
            )

        # ─── WEB FLOW (COOKIE-BASED) ─────────────────
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response({'success': True}, status=status.HTTP_200_OK)
        clear_auth_cookies(response)
        return response


class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @extend_schema(
        operation_id='signup',
        tags=['Auth'],
        request=SignupRequestSerializer,
        responses={
            201: SignupResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        form = SignUpForm(request.data)
        if form.is_valid():
            user = form.save()

            # detect device type
            device = request.headers.get('X-Client-Type', 'web')
            if device not in ['mobile', 'web']:
                device = 'web'

            tokens = get_tokens_for_user(user)

            response = Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_201_CREATED)

            set_auth_cookies(response, tokens)
            return response

        return Response(
            {'errors': form.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


# Minimal serializer for TokenRefreshCookieView request body documentation.
# The actual refresh token is read from the HttpOnly cookie, so the request
# body is intentionally empty — this just satisfies drf-spectacular.
class _EmptyRequestSerializer(drf_serializers.Serializer):
    """No request body — refresh token is read from cookie."""
    pass


class TokenRefreshCookieView(APIView):
    """Replaces SimpleJWT's TokenRefreshView — reads from cookie."""
    permission_classes = [AllowAny]
    authentication_classes = []
    @extend_schema(
        operation_id='token_refresh',
        tags=['Auth'],
        request=_EmptyRequestSerializer,
        responses=TokenRefreshResponseSerializer
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'No refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            refresh = RefreshToken(refresh_token)
            tokens = {
                'access': str(refresh.access_token),
                'refresh': str(refresh),   # rotated
            }
        except TokenError:
            return Response(
                {'error': 'Invalid or expired refresh token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response({'success': True}, status=status.HTTP_200_OK)
        set_auth_cookies(response, tokens)
        return response


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @extend_schema(
        operation_id='password_reset',
        tags=['Auth'],
        request=PasswordResetRequestSerializer,
        responses=PasswordResetResponseSerializer
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(request, user)
        except User.DoesNotExist:
            pass  # silent fail — security best practice
        return Response({'message': 'If that email exists, a reset link was sent.'})

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='get_user_profile',
        tags=['User'],
        responses=MeResponseSerializer
    )
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
        })
        
        
        
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @extend_schema(
        operation_id='password_reset_confirm',
        tags=['Auth'],
        request=PasswordResetConfirmRequestSerializer,
        responses={
            200: PasswordResetConfirmResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        }
    )
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Link is invalid or expired. Please request a new password reset link.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        form = SetPasswordForm(user, request.data)
        if not form.is_valid():
            return Response(
                {'errors': form.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = form.save()

        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Password reset successful.',
            'tokens': tokens
        }, status=status.HTTP_200_OK)

class DeactivateAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='deactivate_account',
        tags=['Account'],
        request=DeactivateAccountRequestSerializer,
        responses={
            200: SuccessResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        serializer = DeactivateAccountRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        password = serializer.validated_data.get('password')
        if not request.user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        user = request.user
        if hasattr(user, 'deactivate') and callable(user.deactivate):
            user.deactivate()
        else:
            user.is_active = False
            user.deactivated_at = timezone.now()
            user.save(update_fields=['is_active', 'deactivated_at'])

        response = Response({'success': True, 'message': 'Account deactivated.'})
        clear_auth_cookies(response)
        return response


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='delete_account',
        tags=['Account'],
        request=DeleteAccountRequestSerializer,
        responses={
            200: SuccessResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request):
        serializer = DeleteAccountRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        password = serializer.validated_data.get('password')
        if not request.user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass

        user = request.user
        if hasattr(user, 'soft_delete') and callable(user.soft_delete):
            user.soft_delete()
        else:
            user.is_deleted = True
            user.deleted_at = timezone.now()
            user.is_active = False
            user.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])

        response = Response({'success': True, 'message': 'Account deleted.'})
        clear_auth_cookies(response)
        return response


class ReactivateConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id='reactivate_confirm',
        tags=['Account'],
        responses={
            200: ReactivateResponseSerializer,
            400: ErrorResponseSerializer,
        }
    )
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response(
                {'error': 'Invalid reactivation link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not reactivation_token.check_token(user, token):
            return Response(
                {'error': 'Link is invalid or expired. Please request a new reactivation link.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_active:
            return Response(
                {'error': 'Account is already active. Please log in.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_deleted:
            user.restore()
        else:
            user.reactivate()

        tokens = get_tokens_for_user(user)
        response = Response({
            'message': 'Account reactivated successfully.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        }, status=status.HTTP_200_OK)
        set_auth_cookies(response, tokens)
        return response