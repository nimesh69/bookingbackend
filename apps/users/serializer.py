from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from drf_spectacular.utils import extend_schema_field

User = get_user_model()


# ────────────────────────────────────────────────────────────────────────────
# Request Serializers (Input Validation)
# ────────────────────────────────────────────────────────────────────────────


class LoginRequestSerializer(serializers.Serializer):
    """Request serializer for login endpoint"""
    username = serializers.CharField(
        max_length=150,
        help_text="Username or email"
    )
    password = serializers.CharField(
        write_only=True,
        help_text="User password"
    )


class SignupRequestSerializer(serializers.Serializer):
    """Request serializer for signup endpoint"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False, allow_blank=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request serializer for password reset"""
    email = serializers.EmailField(help_text="Email address associated with account")


class PasswordResetConfirmRequestSerializer(serializers.Serializer):
    """Request serializer for password reset confirmation"""
    new_password1 = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="New password"
    )
    new_password2 = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Confirm new password"
    )


class DeactivateAccountRequestSerializer(serializers.Serializer):
    """Request serializer for account deactivation"""
    password = serializers.CharField(
        write_only=True,
        help_text="Current password for confirmation"
    )


class DeleteAccountRequestSerializer(serializers.Serializer):
    """Request serializer for account deletion"""
    password = serializers.CharField(
        write_only=True,
        help_text="Current password for confirmation"
    )


class LogoutRequestSerializer(serializers.Serializer):
    """Request serializer for logout (mobile)"""
    refresh = serializers.CharField(
        required=False,
        help_text="Refresh token to blacklist (mobile only)"
    )


class TokenRefreshRequestSerializer(serializers.Serializer):
    """Request serializer for token refresh"""
    # No request body needed - uses cookie for web, header for mobile


# ────────────────────────────────────────────────────────────────────────────
# Response Serializers (Output)
# ────────────────────────────────────────────────────────────────────────────


class UserSerializer(serializers.ModelSerializer):
    """User profile serializer - no password"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'avatar', 'role', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserDetailSerializer(serializers.Serializer):
    """Detailed user response with nested structure"""
    id = serializers.UUIDField()
    name = serializers.CharField()
    username = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(allow_null=True)
    avatar = serializers.URLField(allow_null=True)
    role = serializers.CharField()
    createdAt = serializers.DateTimeField()


class TokenResponseSerializer(serializers.Serializer):
    """JWT token response"""
    access = serializers.CharField(help_text="Access token")
    refresh = serializers.CharField(help_text="Refresh token")


class LoginResponseSerializer(serializers.Serializer):
    """Response serializer for login endpoint"""
    user = UserDetailSerializer()
    access = serializers.CharField(help_text="Access token (mobile only)")
    refresh = serializers.CharField(help_text="Refresh token (mobile only)")


class _SignupUserSerializer(serializers.Serializer):
    id = serializers.CharField()
    username = serializers.CharField()
    email = serializers.EmailField()


class SignupResponseSerializer(serializers.Serializer):
    """Response serializer for signup endpoint"""
    user = serializers.SerializerMethodField()

    @extend_schema_field(_SignupUserSerializer)
    def get_user(self, obj) -> dict:
        return {
            'id': str(obj.id),
            'username': obj.username,
            'email': obj.email,
        }


class PasswordResetResponseSerializer(serializers.Serializer):
    """Response for password reset request"""
    message = serializers.CharField()


class PasswordResetConfirmResponseSerializer(serializers.Serializer):
    """Response for password reset confirmation"""
    message = serializers.CharField()
    tokens = TokenResponseSerializer(required=False)


class SuccessResponseSerializer(serializers.Serializer):
    """Generic success response"""
    success = serializers.BooleanField()
    message = serializers.CharField(required=False)


class MeResponseSerializer(serializers.Serializer):
    """Response for /me endpoint"""
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()


class WsTicketResponseSerializer(serializers.Serializer):
    """WebSocket ticket response"""
    ticket = serializers.CharField(help_text="Single-use WebSocket ticket (valid 30 seconds)")


class ErrorResponseSerializer(serializers.Serializer):
    """Error response serializer"""
    error = serializers.CharField()
    message = serializers.CharField(required=False)


class InactiveAccountResponseSerializer(serializers.Serializer):
    """Response when account is inactive"""
    error = serializers.CharField(default="account_inactive")
    message = serializers.CharField(default="Account is inactive. Reactivation email sent.")


class ReactivateResponseSerializer(serializers.Serializer):
    """Response for account reactivation"""
    message = serializers.CharField()
    user = UserSerializer()


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Response for token refresh"""
    success = serializers.BooleanField()