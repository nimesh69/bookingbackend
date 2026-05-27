import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from .save_image import venue_cover_path, venue_verification_path, turf_image_path

User = get_user_model()


class BaseModel(models.Model):
    """Abstract base model with common fields"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ──────────────────────────────────────────────
# VENUE — one physical location (shared address & amenities)
# ──────────────────────────────────────────────

class Venue(BaseModel):
    """
    A physical location owned by one owner.
    Address and amenities are shared across all turfs inside.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='venues')
    name = models.CharField(max_length=200, help_text="e.g. KTM Sports Hub")
    location = models.CharField(max_length=255, help_text="Physical address")
    amenities = models.JSONField(
        default=dict,
        help_text="Shared facilities e.g. {'parking': true, 'lights': true, 'washroom': true}"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Soft delete timestamp")
    cover_image = models.ImageField(
    upload_to=venue_cover_path,
    null=True,
    blank=True
    )
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Venue"
        verbose_name_plural = "Venues"

    def __str__(self):
        return f"{self.name} — {self.location}"


# ──────────────────────────────────────────────
# Venue owner verification
# ──────────────────────────────────────────────


class VenueVerification(BaseModel):
    venue = models.OneToOneField(
        Venue,
        on_delete=models.CASCADE,
        related_name='verification'
    )

    citizenship_front = models.FileField(
        upload_to=venue_verification_path
    )

    citizenship_back = models.FileField(
        upload_to=venue_verification_path
    )

    pan_card = models.FileField(
        upload_to=venue_verification_path
    )

    business_registration = models.FileField(
        upload_to=venue_verification_path
    )

    verified = models.BooleanField(default=False)

    verified_at = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(blank=True)
# ──────────────────────────────────────────────
# TURF — individual court/field inside a Venue
# ──────────────────────────────────────────────

class Turf(BaseModel):
    """
    A single court or field inside a Venue.
    Each turf can have its own sport, price, hours, name, description, and images.
    """
    SPORT_CHOICES = (
        ('futsal', 'Futsal'),
        ('basketball', 'Basketball'),
        ('badminton', 'Badminton'),
        ('cricket', 'Cricket'),
        ('volleyball', 'Volleyball'),
        ('tennis', 'Tennis'),
        ('pickleball', 'Pickleball'),
        ('table_tennis', 'Table Tennis'),
    )
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='turfs')
    sport = models.CharField(max_length=20, choices=SPORT_CHOICES)
    name = models.CharField(max_length=200, help_text="e.g. Court A - Futsal")
    description = models.TextField(blank=True)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    max_players = models.IntegerField(validators=[MinValueValidator(1)])
    court_count = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Number of courts available for this sport"
    )
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    avg_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="Cached average rating — update via signal or periodic task"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Soft delete timestamp")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Turf"
        verbose_name_plural = "Turfs"

    def __str__(self):
        return f"{self.venue.name} — {self.name} ({self.get_sport_display()})"


# ──────────────────────────────────────────────
# TURF IMAGE
# ──────────────────────────────────────────────

class TurfImage(BaseModel):
    """Images for an individual turf/court"""
    id  = models.AutoField(primary_key=True)
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=turf_image_path)
    order = models.PositiveIntegerField(default=0, help_text="Display order, lower = first")

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Turf Image"
        verbose_name_plural = "Turf Images"

    def __str__(self):
        return f"Image for {self.turf.name}"


# ──────────────────────────────────────────────
# REVIEW — clients review individual turfs
# ──────────────────────────────────────────────

class TurfReview(BaseModel):
    """Client reviews on a turf. avg_rating on Turf is cached from these."""
    id = models.AutoField(primary_key=True)
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='reviews')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turf_reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('turf', 'client')  # one review per client per turf
        ordering = ['-created_at']
        verbose_name = "Turf Review"
        verbose_name_plural = "Turf Reviews"

    def __str__(self):
        return f"{self.client.email} → {self.turf.name} ({self.rating}★)"