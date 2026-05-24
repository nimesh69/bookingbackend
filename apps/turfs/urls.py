from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VenueViewSet, TurfViewSet

router = DefaultRouter()
router.register(r'venues', VenueViewSet, basename='venue')
router.register(r'turfs', TurfViewSet, basename='turf')

urlpatterns = [
    path('', include(router.urls)),
]
