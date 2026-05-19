import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.turfs.models import Turf

User = get_user_model()


class BaseModel(models.Model):
    """Abstract base model with timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Booking(BaseModel):
    """Booking model for turf reservations"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='bookings')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    match = models.ForeignKey('matches.Match', on_delete=models.SET_NULL, 
                             null=True, blank=True, related_name='bookings',
                             help_text="Associated match if this booking is linked to a match")
    
    class Meta:
        unique_together = ('turf', 'date', 'start_time')
        ordering = ['-created_at']
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['turf', 'date']),
        ]
    
    def __str__(self):
        return f"Booking {self.id} - {self.turf.turf.name} on {self.date}"
