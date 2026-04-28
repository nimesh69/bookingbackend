from django.db import models
from django.contrib.auth import get_user_model
from bookings.models import Booking

User = get_user_model()

class ChatRoom(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='chat_room')
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='client_chat_rooms')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat - {self.client.username} & {self.owner.username}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.room.id}"
