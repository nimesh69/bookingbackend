from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import User, BlacklistedToken, DeviceToken

@admin.register(User)
class UserAdmin(BaseUserAdmin, UnfoldModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'created_at')
    list_filter = ('role', 'is_verified', 'is_active', 'created_at')
    list_per_page = 25
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {'fields': ('username', 'password', 'id')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar')}),
        ('Role & Verification', {'fields': ('role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('created_at', 'updated_at', 'last_login')}),
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_login')


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(UnfoldModelAdmin):
    list_display = ('id', 'expires_at', 'created_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('token',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Token Info', {'fields': ('id', 'token')}),
        ('Expiration', {'fields': ('expires_at',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(DeviceToken)
class DeviceTokenAdmin(UnfoldModelAdmin):
    list_display = ('user', 'platform', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active', 'created_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Device Info', {'fields': ('id', 'platform', 'token', 'is_active')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
