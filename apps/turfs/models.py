import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class BaseModel(models.Model):
    """Abstract base model with timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Turf(BaseModel):
    """Sports turf/venue model"""
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turfs')
    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    amenities = models.JSONField(default=dict, help_text="e.g., lights, parking, washroom")
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, 
                                     validators=[MinValueValidator(0), MaxValueValidator(5)],
                                     help_text="Cached average rating")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Soft delete timestamp")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Turf"
        verbose_name_plural = "Turfs"
    
    def __str__(self):
        return f"{self.name} (Owner: {self.owner.email})"


class TurfSport(BaseModel):
    """Sports offered at each turf"""
    SPORT_CHOICES = (
        ('futsal', 'Futsal'),
        ('basketball', 'Basketball'),
        ('badminton', 'Badminton'),
        ('cricket', 'Cricket'),
        ('volleyball', 'Volleyball'),
        ('tennis', 'Tennis'),
    )
    
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='sports')
    sport = models.CharField(max_length=20, choices=SPORT_CHOICES)
    price_per_hour = models.DecimalField(max_digits=10, decimal_places=2)
    max_players = models.IntegerField()
    court_count = models.IntegerField(help_text="Number of courts available")
    
    class Meta:
        unique_together = ('turf', 'sport')
        verbose_name = "Turf Sport"
        verbose_name_plural = "Turf Sports"
        ordering = ['turf', 'sport']
    
    def __str__(self):
        return f"{self.turf.name} - {self.get_sport_display()}"


class TurfImage(BaseModel):
    """Images for turfs"""
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='turf_images/')
    is_cover = models.BooleanField(default=False, help_text="Display as cover image")
    order = models.IntegerField(default=0, help_text="Display order for images")
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Turf Image"
        verbose_name_plural = "Turf Images"
    
    def __str__(self):
        return f"Image for {self.turf.name}"
