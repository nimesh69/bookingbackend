from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import Venue, VenueImage

class VenueImageInline(TabularInline):
    model = VenueImage
    extra = 1
    fields = ('image', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

@admin.register(Venue)
class VenueAdmin(UnfoldModelAdmin):
    list_display = ('name', 'owner', 'sport_type', 'price_per_hour', 'rating_avg', 'created_at')
    list_filter = ('sport_type', 'created_at')
    list_per_page = 20
    search_fields = ('name', 'location', 'owner__username', 'description')
    readonly_fields = ('rating_avg', 'created_at', 'updated_at')
    inlines = (VenueImageInline,)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'sport_type')
        }),
        ('Description & Location', {
            'fields': ('description', 'location', 'latitude', 'longitude')
        }),
        ('Business Hours & Pricing', {
            'fields': ('opening_time', 'closing_time', 'price_per_hour')
        }),
        ('Rating & Metadata', {
            'fields': ('rating_avg', 'created_at', 'updated_at')
        }),
    )

@admin.register(VenueImage)
class VenueImageAdmin(UnfoldModelAdmin):
    list_display = ('venue', 'image', 'uploaded_at')
    list_filter = ('uploaded_at',)
    list_per_page = 50
    search_fields = ('venue__name',)
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('Image Information', {
            'fields': ('venue', 'image', 'uploaded_at')
        }),
    )
