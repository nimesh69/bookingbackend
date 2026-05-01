import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.bookings.models import Booking

User = get_user_model()


class BaseModel(models.Model):
    """Abstract base model with timestamps"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class ChatRoom(models.Model):
    """Chat room for booking communication"""
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='chat_room')
    is_active = models.BooleanField(default=True, help_text="Set to false after booking event ends")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When the chat was closed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Chat Room"
        verbose_name_plural = "Chat Rooms"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat Room for Booking {self.booking.id}"


class Message(BaseModel):
    """Chat messages in a room"""
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('system', 'System'),
    )
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    msg_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.email} in room {self.room.id}"
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.room.id}"
