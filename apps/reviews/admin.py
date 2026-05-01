from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Review


@admin.register(Review)
class ReviewAdmin(UnfoldModelAdmin):
    list_display = ('turf', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'turf', 'created_at')
    list_per_page = 30
    search_fields = ('turf__name', 'user__email', 'comment', 'booking__id')
    readonly_fields = ('id', 'booking', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('id', 'booking', 'user', 'turf', 'rating')
        }),
        ('Feedback', {
            'fields': ('comment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
