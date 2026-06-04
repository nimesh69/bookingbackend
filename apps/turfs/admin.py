from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import Venue, Turf, TurfImage, TurfReview, VenueVerification
from django.utils import timezone
from django import forms

# ── Inlines ───────────────────────────────────────────────────────────────────


class TurfInline(TabularInline):
    model = Turf
    extra = 0
    fields = (
        "name",
        "sport",
        "price_per_hour",
        "opening_time",
        "closing_time",
        "status",
    )
    show_change_link = True  # click through to full Turf form


class TurfImageInline(TabularInline):
    model = TurfImage
    extra = 0
    fields = ("image", "order")


class TurfReviewInline(TabularInline):
    model = TurfReview
    extra = 0
    fields = ("client", "rating", "comment", "created_at")
    readonly_fields = (
        "client",
        "rating",
        "comment",
        "created_at",
    )  # reviews shouldn't be edited in admin


class VenueVerificationInline(TabularInline):
    model = VenueVerification
    extra = 0
    fields = ("verified", "verified_at", "rejection_reason")
    can_delete = False


# ── Bulk Actions ──────────────────────────────────────────────────────────────


def make_active(modeladmin, request, queryset):
    """Bulk action to change status from draft to active"""
    venue_count = 0
    turf_count = 0
    for venue in queryset.filter(status="draft"):
        venue.status = "active"
        venue.save()
        venue_count += 1
        # Cascade to related turfs
        turf_count += venue.turfs.all().update(status="active")
    modeladmin.message_user(
        request, f"{venue_count} venues activated. {turf_count} turfs updated."
    )


make_active.short_description = "Activate selected (change draft to active)"


def make_inactive(modeladmin, request, queryset):
    """Bulk action to change status to inactive"""
    venue_count = 0
    turf_count = 0
    for venue in queryset:
        venue.status = "inactive"
        venue.save()
        venue_count += 1
        # Cascade to related turfs
        turf_count += venue.turfs.all().update(status="inactive")
    modeladmin.message_user(
        request, f"{venue_count} venues marked as inactive. {turf_count} turfs updated."
    )


make_inactive.short_description = "Mark as inactive"


# ── Venue ─────────────────────────────────────────────────────────────────────


@admin.register(Venue)
class VenueAdmin(UnfoldModelAdmin):
    list_display = (
        "name",
        "owner",
        "location",
        "status",
        "has_verification",
        "created_at",
    )
    list_filter = ("status", "created_at")
    list_per_page = 20
    search_fields = ("name", "location", "owner__email")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (VenueVerificationInline, TurfInline)
    actions = [make_active, make_inactive]

    fieldsets = (
        ("Basic Information", {"fields": ("id", "name", "owner")}),
        ("Location & Amenities", {"fields": ("location", "amenities")}),
        ("Cover Image", {"fields": ("cover_image",)}),
        ("Status", {"fields": ("status", "deleted_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def has_verification(self, obj):
        """Display verification status"""
        verification = hasattr(obj, "verification") and obj.verification
        if verification:
            return f"{'✓ Verified' if verification.verified else '⏳ Pending'}"
        return "❌ Not Started"

    has_verification.short_description = "Verification"

    def save_model(self, request, obj, form, change):
        """Override save_model to cascade status changes to related turfs"""
        if change:  # Only if editing an existing object
            try:
                original_obj = Venue.objects.get(pk=obj.pk)
                if original_obj.status != obj.status:
                    # Status has changed, cascade to related turfs
                    updated_turfs = obj.turfs.all().update(status=obj.status)
                    self.message_user(
                        request,
                        f"Venue status changed to '{obj.status}'. {updated_turfs} turf(s) updated.",
                    )
            except Venue.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


# ── Venue Verification ────────────────────────────────────────────────────────


@admin.register(VenueVerification)
class VenueVerificationAdmin(UnfoldModelAdmin):
    list_display = ("venue_name", "verified", "verified_at", "created_at")
    list_filter = ("verified", "created_at", "venue__status")
    list_per_page = 20
    search_fields = ("venue__name", "venue__owner__email")
    readonly_fields = ("id", "created_at", "updated_at", "verified_at")
    actions = ["approve_verification", "reject_verification"]

    fieldsets = (
        ("Venue", {"fields": ("id", "venue")}),
        ("Citizenship", {"fields": ("citizenship_front", "citizenship_back")}),
        ("Business Documents", {"fields": ("pan_card", "business_registration")}),
        (
            "Verification Status",
            {"fields": ("verified", "verified_at", "rejection_reason")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def venue_name(self, obj):
        return obj.venue.name

    venue_name.short_description = "Venue"

    def save_model(self, request, obj, form, change):
        if obj.verified and not obj.verified_at:
            obj.verified_at = timezone.now()
        elif not obj.verified:
            obj.verified_at = None
        super().save_model(request, obj, form, change)
        VenueVerification.objects.filter(pk=obj.pk).update(verified_at=obj.verified_at)

    def approve_verification(self, request, queryset):
        updated = 0
        for verification in queryset:
            verification.verified = True
            verification.verified_at = timezone.now()
            verification.rejection_reason = ""
            verification.save()
            verification.venue.status = "active"
            verification.venue.save()
            # Cascade to turfs
            verification.venue.turfs.all().update(status="active")
            updated += 1
        self.message_user(
            request, f"{updated} venues verified, activated, and turfs updated."
        )

    approve_verification.short_description = (
        "Approve verification & activate venue + turfs"
    )

    def reject_verification(self, request, queryset):
        updated = 0
        for verification in queryset.exclude(verified=True):
            verification.verified = False
            verification.save()
            verification.venue.status = "inactive"
            verification.venue.save()
            verification.venue.turfs.all().update(status="inactive")
            updated += 1
        self.message_user(
            request, f"{updated} venues rejected and marked inactive with turfs."
        )

    reject_verification.short_description = (
        "Reject verification & deactivate venue + turfs"
    )


# ── Turf ──────────────────────────────────────────────────────────────────────


@admin.register(Turf)
class TurfAdmin(UnfoldModelAdmin):
    list_display = (
        "name",
        "venue",
        "sport",
        "price_per_hour",
        "status",
        "avg_rating",
        "created_at",
    )
    list_filter = ("status", "sport", "created_at")
    list_per_page = 20
    search_fields = ("name", "venue__name", "venue__owner__email", "description")
    readonly_fields = ("id", "avg_rating", "created_at", "updated_at")
    inlines = (TurfImageInline, TurfReviewInline)
    actions = [make_active, make_inactive]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("id", "venue", "name", "description", "sport")},
        ),
        (
            "Pricing & Capacity",
            {"fields": ("price_per_hour", "max_players", "court_count")},
        ),
        ("Operating Hours", {"fields": ("opening_time", "closing_time")}),
        ("Status & Rating", {"fields": ("status", "avg_rating", "deleted_at")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


# ── Turf Image ────────────────────────────────────────────────────────────────


@admin.register(TurfImage)
class TurfImageAdmin(UnfoldModelAdmin):
    list_display = ("turf", "order", "created_at")
    list_filter = ("created_at",)
    search_fields = ("turf__name", "turf__venue__name")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Image Info", {"fields": ("id", "turf", "image", "order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


# ── Turf Review ───────────────────────────────────────────────────────────────


@admin.register(TurfReview)
class TurfReviewAdmin(UnfoldModelAdmin):
    list_display = ("turf", "client", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("turf__name", "client__email", "comment")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Review Info", {"fields": ("id", "turf", "client", "rating", "comment")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
