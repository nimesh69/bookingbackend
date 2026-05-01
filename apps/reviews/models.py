import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.bookings.models import Booking
from apps.turfs.models import Turf

User = get_user_model()


class BaseModel(models.Model):
    """Abstract base model with timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Review(BaseModel):
    """Review model for turfs"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review', unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    
    class Meta:
        unique_together = ('booking', 'user', 'turf')
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
    
    def __str__(self):
        return f"Review by {self.user.email} for {self.turf.name} - {self.rating}★"
