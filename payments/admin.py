from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(UnfoldModelAdmin):
    list_display = ('id', 'booking', 'amount', 'payment_method', 'status', 'paid_at')
    list_filter = ('status', 'payment_method', 'created_at')
    list_per_page = 25
    search_fields = ('booking__id', 'transaction_id', 'booking__venue__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Reference', {
            'fields': ('booking',)
        }),
        ('Payment Details', {
            'fields': ('amount', 'payment_method', 'transaction_id')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'paid_at', 'created_at', 'updated_at')
        }),
    )
