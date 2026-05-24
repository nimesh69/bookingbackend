from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import Venue, Turf, TurfImage, TurfReview, VenueVerification


# ── Inlines ───────────────────────────────────────────────────────────────────

class TurfInline(TabularInline):
    model = Turf
    extra = 1
    fields = ('name', 'sport', 'price_per_hour', 'opening_time', 'closing_time', 'status')
    show_change_link = True  # click through to full Turf form


class TurfImageInline(TabularInline):
    model = TurfImage
    extra = 1
    fields = ('image', 'order')


class TurfReviewInline(TabularInline):
    model = TurfReview
    extra = 0
    fields = ('client', 'rating', 'comment', 'created_at')
    readonly_fields = ('client', 'rating', 'comment', 'created_at')  # reviews shouldn't be edited in admin


class VenueVerificationInline(TabularInline):
    model = VenueVerification
    extra = 0
    fields = ('verified', 'verified_at', 'rejection_reason')
    can_delete = False


# ── Bulk Actions ──────────────────────────────────────────────────────────────


def make_active(modeladmin, request, queryset):
    """Bulk action to change status from draft to active"""
    updated = queryset.filter(status='draft').update(status='active')
    modeladmin.message_user(request, f'{updated} venues/turfs activated.')
make_active.short_description = "Activate selected (change draft to active)"


def make_inactive(modeladmin, request, queryset):
    """Bulk action to change status to inactive"""
    updated = queryset.update(status='inactive')
    modeladmin.message_user(request, f'{updated} venues/turfs marked as inactive.')
make_inactive.short_description = "Mark as inactive"


# ── Venue ─────────────────────────────────────────────────────────────────────

@admin.register(Venue)
class VenueAdmin(UnfoldModelAdmin):
    list_display = ('name', 'owner', 'location', 'status', 'has_verification', 'created_at')
    list_filter = ('status', 'created_at')
    list_per_page = 20
    search_fields = ('name', 'location', 'owner__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (VenueVerificationInline, TurfInline)
    actions = [make_active, make_inactive]

    fieldsets = (
        ('Basic Information', {'fields': ('id', 'name', 'owner')}),
        ('Location & Amenities', {'fields': ('location', 'amenities')}),
        ('Cover Image', {'fields': ('cover_image',)}),
        ('Status', {'fields': ('status', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def has_verification(self, obj):
        """Display verification status"""
        verification = hasattr(obj, 'verification') and obj.verification
        if verification:
            return f"{'✓ Verified' if verification.verified else '⏳ Pending'}"
        return "❌ Not Started"
    has_verification.short_description = "Verification"


# ── Venue Verification ────────────────────────────────────────────────────────

@admin.register(VenueVerification)
class VenueVerificationAdmin(UnfoldModelAdmin):
    list_display = ('venue_name', 'verified', 'verified_at', 'created_at')
    list_filter = ('verified', 'created_at')
    list_per_page = 20
    search_fields = ('venue__name', 'venue__owner__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    actions = ['approve_verification', 'reject_verification']

    fieldsets = (
        ('Venue', {'fields': ('id', 'venue')}),
        ('Citizenship', {'fields': ('citizenship_front', 'citizenship_back')}),
        ('Business Documents', {'fields': ('pan_card', 'business_registration')}),
        ('Verification Status', {'fields': ('verified', 'verified_at', 'rejection_reason')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def venue_name(self, obj):
        return obj.venue.name
    venue_name.short_description = "Venue"

    def approve_verification(self, request, queryset):
        """Bulk action to approve venue verification"""
        from django.utils import timezone
        updated = 0
        for verification in queryset:
            verification.verified = True
            verification.verified_at = timezone.now()
            verification.rejection_reason = ""
            verification.save()
            # Also activate the venue
            verification.venue.status = 'active'
            verification.venue.save()
            updated += 1
        self.message_user(request, f'{updated} venues verified and activated.')
    approve_verification.short_description = "Approve verification & activate venue"

    def reject_verification(self, request, queryset):
        """Bulk action to reject venue verification"""
        # This would typically show a form to enter rejection reason
        # For now, we'll just change status to inactive
        updated = queryset.exclude(verified=True).update(verified=False)
        self.message_user(request, f'{updated} venues marked for rejection.')
    reject_verification.short_description = "Mark for rejection"


# ── Turf ──────────────────────────────────────────────────────────────────────

@admin.register(Turf)
class TurfAdmin(UnfoldModelAdmin):
    list_display = ('name', 'venue', 'sport', 'price_per_hour', 'status', 'avg_rating', 'created_at')
    list_filter = ('status', 'sport', 'created_at')
    list_per_page = 20
    search_fields = ('name', 'venue__name', 'venue__owner__email', 'description')
    readonly_fields = ('id', 'avg_rating', 'created_at', 'updated_at')
    inlines = (TurfImageInline, TurfReviewInline)
    actions = [make_active, make_inactive]

    fieldsets = (
        ('Basic Information', {'fields': ('id', 'venue', 'name', 'description', 'sport')}),
        ('Pricing & Capacity', {'fields': ('price_per_hour', 'max_players', 'court_count')}),
        ('Operating Hours', {'fields': ('opening_time', 'closing_time')}),
        ('Status & Rating', {'fields': ('status', 'avg_rating', 'deleted_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


# ── Turf Image ────────────────────────────────────────────────────────────────

@admin.register(TurfImage)
class TurfImageAdmin(UnfoldModelAdmin):
    list_display = ('turf', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('turf__name', 'turf__venue__name')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        ('Image Info', {'fields': ('id', 'turf', 'image', 'order')}),
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