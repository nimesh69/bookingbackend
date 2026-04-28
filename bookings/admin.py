from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import TimeSlot, Booking

@admin.register(TimeSlot)
class TimeSlotAdmin(UnfoldModelAdmin):
    list_display = ('venue', 'date', 'start_time', 'end_time', 'is_available')
    list_filter = ('is_available', 'date', 'venue')
    list_per_page = 50
    search_fields = ('venue__name',)
    readonly_fields = ('created_at',)
    list_editable = ('is_available',)
    
    fieldsets = (
        ('Slot Information', {
            'fields': ('venue', 'date', 'start_time', 'end_time')
        }),
        ('Availability', {
            'fields': ('is_available', 'created_at')
        }),
    )

@admin.register(Booking)
class BookingAdmin(UnfoldModelAdmin):
    list_display = ('id', 'venue', 'client', 'date', 'status', 'payment_status', 'total_price', 'created_at')
    list_filter = ('status', 'payment_status', 'date', 'created_at')
    list_per_page = 25
    search_fields = ('venue__name', 'client__username', 'client__email', 'id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('venue', 'client', 'date', 'start_time', 'end_time')
        }),
        ('Pricing & Status', {
            'fields': ('total_price', 'status', 'payment_status')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
