# signals.py
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TurfReview

@receiver(post_save, sender=TurfReview)
def update_avg_rating(sender, instance, **kwargs):
    avg = instance.turf.reviews.aggregate(Avg('rating'))['rating__avg']
    instance.turf.avg_rating = avg or 0
    instance.turf.save(update_fields=['avg_rating'])