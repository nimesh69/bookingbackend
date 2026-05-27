import os
import uuid

def venue_cover_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'venues/{instance.id}/cover/{uuid.uuid4()}{ext}'


def venue_verification_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'venues/{instance.venue.id}/verification/{uuid.uuid4()}{ext}'


def turf_image_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'venues/{instance.turf.venue.id}/turfs/{instance.turf.id}/{uuid.uuid4()}{ext}'