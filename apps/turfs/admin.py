from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import Turf, TurfSport, TurfImage


class TurfImageInline(TabularInline):
    model = TurfImage
    extra = 1
    fields = ('image', 'is_cover', 'order')


class TurfSportInline(TabularInline):
    model = TurfSport
    extra = 1
    fields = ('sport', 'price_per_hour', 'max_players', 'court_count')


@admin.register(Turf)
class TurfAdmin(UnfoldModelAdmin):
    list_display = ('name', 'owner', 'location', 'is_active', 'avg_rating', 'created_at')
    list_filter = ('is_active', 'created_at', 'owner')
    list_per_page = 20
    search_fields = ('name', 'location', 'owner__email', 'description')
    readonly_fields = ('id', 'avg_rating', 'created_at', 'updated_at')
    inlines = (TurfImageInline, TurfSportInline)
    
    fieldsets = (
        ('Basic Information', {'fields': ('id', 'name', 'description', 'owner')}),
        ('Location', {'fields': ('location', 'latitude', 'longitude')}),
        ('Operating Hours', {'fields': ('opening_time', 'closing_time')}),
        ('Additional Info', {'fields': ('amenities', 'is_active', 'avg_rating', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(TurfSport)
class TurfSportAdmin(UnfoldModelAdmin):
    list_display = ('turf', 'sport', 'price_per_hour', 'max_players', 'court_count')
    list_filter = ('sport', 'turf', 'created_at')
    search_fields = ('turf__name', 'sport')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Turf & Sport', {'fields': ('id', 'turf', 'sport')}),
        ('Pricing & Capacity', {'fields': ('price_per_hour', 'max_players', 'court_count')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(TurfImage)
class TurfImageAdmin(UnfoldModelAdmin):
    list_display = ('turf', 'is_cover', 'order', 'created_at')
    list_filter = ('is_cover', 'turf', 'created_at')
    search_fields = ('turf__name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Image Info', {'fields': ('id', 'turf', 'image', 'is_cover', 'order')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
