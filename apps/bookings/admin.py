from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(UnfoldModelAdmin):
    list_display = ('id', 'user', 'turf', 'date', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'date', 'created_at', 'turf__venue__owner')
    list_per_page = 25
    search_fields = ('user__email', 'turf__name', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Info', {
            'fields': ('id', 'user', 'turf_sport')
        }),
        ('Date & Time', {
            'fields': ('date', 'start_time', 'end_time', 'duration_hours')
        }),
        ('Pricing & Status', {
            'fields': ('total_price', 'status', 'match')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
