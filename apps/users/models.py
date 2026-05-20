import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class BaseModel(models.Model):
    """Abstract base model with timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class User(AbstractUser):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('player', 'Player'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    is_verified = models.BooleanField(default=False, help_text="Email verified status")
    avatar = models.ImageField(upload_to='avatar/',  default = 'avatar/default.jpg', blank=True, null=True, help_text="Profile photo")
    device = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"


class BlacklistedToken(BaseModel):
    """Store blacklisted JWT tokens for logout"""
    token = models.CharField(max_length=500, unique=True)
    expires_at = models.DateTimeField(help_text="Token expiration time")
    
    class Meta:
        verbose_name = "Blacklisted Token"
        verbose_name_plural = "Blacklisted Tokens"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token blacklisted until {self.expires_at}"


class DeviceToken(BaseModel):
    """Store device tokens for push notifications"""
    PLATFORM_CHOICES = (
        ('fcm', 'Firebase Cloud Messaging'),
        ('apns', 'Apple Push Notification Service'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    token = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'token')
        verbose_name = "Device Token"
        verbose_name_plural = "Device Tokens"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.get_platform_display()}"
