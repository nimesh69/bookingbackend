from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import Review

@admin.register(Review)
class ReviewAdmin(UnfoldModelAdmin):
    list_display = ('venue', 'client', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    list_per_page = 30
    search_fields = ('venue__name', 'client__username', 'client__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('venue', 'client', 'rating')
        }),
        ('Feedback', {
            'fields': ('comment',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at')
        }),
    )
