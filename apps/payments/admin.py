from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(UnfoldModelAdmin):
    list_display = ('booking', 'gateway', 'amount', 'status', 'paid_at', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    list_per_page = 25
    search_fields = ('booking__id', 'transaction_id')
    readonly_fields = ('booking', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Payment Details', {
            'fields': ('gateway', 'transaction_id', 'amount')
        }),
        ('Status & Response', {
            'fields': ('status', 'paid_at', 'gateway_response')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
