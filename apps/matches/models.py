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


class Match(BaseModel):
    """Match model for organizing matches"""
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('full', 'Full'),
        ('cancelled', 'Cancelled'),
    )
    
    SKILL_LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('mid', 'Intermediate'),
        ('pro', 'Professional'),
    )
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_matches')
    sport = models.CharField(max_length=50)
    turf = models.ForeignKey(Turf, on_delete=models.SET_NULL, 
                            null=True, blank=True, related_name='matches',
                            help_text="Associated turf, nullable for auto-booking")
    match_date = models.DateField()
    start_time = models.TimeField()
    format = models.CharField(max_length=50, help_text="e.g., 5v5, 3v3, 7v7")
    slots_needed = models.IntegerField(help_text="How many more players needed")
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    location_text = models.CharField(max_length=255, help_text="Area/city description")
    
    class Meta:
        verbose_name = "Match"
        verbose_name_plural = "Matches"
        ordering = ['-match_date', '-start_time']
        indexes = [
            models.Index(fields=['-match_date', 'status']),
        ]
    
    def __str__(self):
        return f"Match {self.id} - {self.sport} on {self.match_date}"


class MatchParticipant(BaseModel):
    """Participants joining a match"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    TEAM_CHOICES = (
        ('A', 'Team A'),
        ('B', 'Team B'),
    )
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_participations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    team = models.CharField(max_length=10, choices=TEAM_CHOICES, null=True, blank=True, help_text="Team assignment")
    
    class Meta:
        unique_together = ('match', 'user')
        verbose_name = "Match Participant"
        verbose_name_plural = "Match Participants"
        ordering = ['status', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} in Match {self.match.id} ({self.get_status_display()})"
