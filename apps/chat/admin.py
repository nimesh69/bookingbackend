from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import ChatRoom, Message


class MessageInline(TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'content', 'msg_type', 'is_read', 'created_at')
    readonly_fields = ('created_at', 'id')
    can_delete = False


@admin.register(ChatRoom)
class ChatRoomAdmin(UnfoldModelAdmin):
    list_display = ('booking', 'is_active', 'closed_at', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_per_page = 25
    search_fields = ('booking__id', 'booking__user__email')
    readonly_fields = ('booking', 'created_at', 'updated_at')
    inlines = (MessageInline,)
    
    fieldsets = (
        ('Chat Information', {
            'fields': ('booking', 'is_active', 'closed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Message)
class MessageAdmin(UnfoldModelAdmin):
    list_display = ('id', 'room', 'sender', 'msg_type', 'is_read', 'created_at')
    list_filter = ('is_read', 'msg_type', 'created_at', 'sender')
    list_per_page = 50
    search_fields = ('room__booking__id', 'sender__email', 'content')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_editable = ('is_read',)
    
    fieldsets = (
        ('Message Details', {
            'fields': ('id', 'room', 'sender', 'content', 'msg_type')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at', 'updated_at')
        }),
    )
