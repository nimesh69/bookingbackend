from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth import get_user_model

User = get_user_model()
from django.core.validators import RegexValidator

alphanumeric_validator = RegexValidator(
    regex=r"^[a-zA-Z0-9]+$", message="Username can only contain letters and numbers."
)


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    last_name = forms.CharField(max_length=30, required=False, help_text="Optional.")
    username = forms.CharField(
        max_length=30,
        validators=[alphanumeric_validator],
        help_text="Letters and numbers only.",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "email",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class CustomPasswordResetForm(PasswordResetForm):
    """Custom Password Reset Form with email existence validation"""

    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def clean_email(self):
        """Validate that the email exists in the database"""
        email = self.cleaned_data.get("email").strip()

        # Check if email exists in User model
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "No user found with this email address. Please register first or check your email."
            )
        return email