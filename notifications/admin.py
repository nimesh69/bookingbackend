from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(UnfoldModelAdmin):
    list_display = ('id', 'user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    list_per_page = 30
    search_fields = ('user__username', 'user__email', 'title', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'title', 'type')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status & Metadata', {
            'fields': ('is_read', 'created_at')
        }),
    )
