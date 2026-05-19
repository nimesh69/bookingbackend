from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import Venue, Turf, TurfImage, TurfReview


# ── Inlines ───────────────────────────────────────────────────────────────────

class TurfInline(TabularInline):
    model = Turf
    extra = 1
    fields = ('name', 'sport', 'price_per_hour', 'opening_time', 'closing_time', 'is_active')
    show_change_link = True  # click through to full Turf form


class TurfImageInline(TabularInline):
    model = TurfImage
    extra = 1
    fields = ('image', 'is_cover', 'order')


class TurfReviewInline(TabularInline):
    model = TurfReview
    extra = 0
    fields = ('client', 'rating', 'comment', 'created_at')
    readonly_fields = ('client', 'rating', 'comment', 'created_at')  # reviews shouldn't be edited in admin


# ── Venue ─────────────────────────────────────────────────────────────────────

@admin.register(Venue)
class VenueAdmin(UnfoldModelAdmin):
    list_display = ('name', 'owner', 'location', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_per_page = 20
    search_fields = ('name', 'location', 'owner__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (TurfInline,)

    fieldsets = (
        ('Basic Information', {'fields': ('id', 'name', 'owner')}),
        ('Location & Amenities', {'fields': ('location', 'amenities')}),
        ('Status', {'fields': ('is_active', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# ── Turf ──────────────────────────────────────────────────────────────────────

@admin.register(Turf)
class TurfAdmin(UnfoldModelAdmin):
    list_display = ('name', 'venue', 'sport', 'price_per_hour', 'is_active', 'avg_rating', 'created_at')
    list_filter = ('is_active', 'sport', 'created_at')
    list_per_page = 20
    search_fields = ('name', 'venue__name', 'venue__owner__email', 'description')
    readonly_fields = ('id', 'avg_rating', 'created_at', 'updated_at')
    inlines = (TurfImageInline, TurfReviewInline)

    fieldsets = (
        ('Basic Information', {'fields': ('id', 'venue', 'name', 'description', 'sport')}),
        ('Pricing & Capacity', {'fields': ('price_per_hour', 'max_players', 'court_count')}),
        ('Operating Hours', {'fields': ('opening_time', 'closing_time')}),
        ('Status & Rating', {'fields': ('is_active', 'avg_rating', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# ── Turf Image ────────────────────────────────────────────────────────────────

@admin.register(TurfImage)
class TurfImageAdmin(UnfoldModelAdmin):
    list_display = ('turf', 'is_cover', 'order', 'created_at')
    list_filter = ('is_cover', 'created_at')
    search_fields = ('turf__name', 'turf__venue__name')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Image Info', {'fields': ('id', 'turf', 'image', 'is_cover', 'order')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# ── Turf Review ───────────────────────────────────────────────────────────────

@admin.register(TurfReview)
class TurfReviewAdmin(UnfoldModelAdmin):
    list_display = ('turf', 'client', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('turf__name', 'client__email', 'comment')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Review Info', {'fields': ('id', 'turf', 'client', 'rating', 'comment')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )