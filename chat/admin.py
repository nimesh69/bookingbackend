from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import ChatRoom, Message

class MessageInline(TabularInline):
    model = Message
    extra = 0
    fields = ('sender', 'message', 'is_read', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = True

@admin.register(ChatRoom)
class ChatRoomAdmin(UnfoldModelAdmin):
    list_display = ('id', 'booking', 'client', 'owner', 'created_at')
    list_filter = ('created_at',)
    list_per_page = 25
    search_fields = ('client__username', 'client__email', 'owner__username', 'booking__id')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (MessageInline,)
    
    fieldsets = (
        ('Chat Information', {
            'fields': ('booking', 'client', 'owner')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Message)
class MessageAdmin(UnfoldModelAdmin):
    list_display = ('id', 'room', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'sender')
    list_per_page = 50
    search_fields = ('room__id', 'sender__username', 'sender__email', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_read',)
    
    fieldsets = (
        ('Message Details', {
            'fields': ('room', 'sender', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
