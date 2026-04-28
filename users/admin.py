from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin, UnfoldModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_verified', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'date_joined')
    list_per_page = 25
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    
    fieldsets = (
        ('Basic Information', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Role & Verification', {'fields': ('role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'phone', 'role'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
