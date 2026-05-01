from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(UnfoldModelAdmin):
    list_display = ('id', 'user', 'title', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    list_per_page = 30
    search_fields = ('user__email', 'title', 'message', 'related_object_id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_editable = ('is_read',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('id', 'user', 'title', 'type')
        }),
        ('Message', {
            'fields': ('message', 'related_object_id')
        }),
        ('Status & Timestamps', {
            'fields': ('is_read', 'created_at', 'updated_at')
        }),
    )
