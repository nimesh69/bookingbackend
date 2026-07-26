from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import os, shutil
from django.db import transaction
from .models import Venue, Turf, TurfImage, TurfReview, VenueVerification
from .serializers import (
    VenueListSerializer, VenueDetailSerializer, VenueCreateUpdateSerializer,
    TurfListSerializer, TurfDetailSerializer, TurfCreateUpdateSerializer,
    TurfImageSerializer, TurfReviewSerializer, VenueVerificationSerializer
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from .checkOwnerPassword import verify_owner_password_or_403
class IsOwnerOrReadOnly:
    """Custom permission: write access only to owner"""
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.owner == request.user


class IsOwnerOrAdmin(BasePermission):
    """
    Permission class: only owner or admin can access
    """
    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Must be owner or admin
        return obj.owner == request.user or request.user.is_staff


class VenueViewSet(viewsets.ModelViewSet):
    """
    API for Venues:
    - GET /api/venues/ — List all venues
    - POST /api/venues/ — Create venue (owner only)
    - GET /api/venues/{id}/ — Venue detail with turfs
    - PATCH /api/venues/{id}/ — Update venue (owner only)
    - DELETE /api/venues/{id}/ — Soft-delete (owner only)
    """
    queryset = Venue.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['location', 'status']
    search_fields = ['name', 'location']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return VenueDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VenueCreateUpdateSerializer
        return VenueListSerializer

    def get_queryset(self):
        """
        Show only non-deleted venues.
        For regular users: only show active venues.
        For authenticated users: show their own venues regardless of status.
        """
        queryset = Venue.objects.filter(deleted_at__isnull=True)
        
        # If it's a list view (not detail), filter by status
        if self.action == 'list':
            # If user is authenticated and accessing 'my_venues', show all their venues
            if self.request.user.is_authenticated:
                # For regular list, only show active venues to app users
                queryset = queryset.filter(status='active')
            else:
                # For anonymous users, show only active venues
                queryset = queryset.filter(status='active')
        
        return queryset

    def perform_create(self, serializer):
        """Set owner to current user"""
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete: set deleted_at instead of hard delete"""
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=True, methods=['post'], url_path='confirm-delete')
    def confirm_delete(self, request, pk=None):
        venue = self.get_object()
        verify_owner_password_or_403(request, venue.owner)
        venue.deleted_at = timezone.now()
        venue.save()
        return Response({'message': 'Venue deleted successfully.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_venues(self, request):
        """Get all venues owned by logged-in user"""
        venues = Venue.objects.filter(
            owner=request.user,
            deleted_at__isnull=True
        )
        serializer = VenueListSerializer(venues, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['get', 'post'],
        permission_classes=[IsOwnerOrAdmin],
        url_path='verification'
    )
    def verification(self, request, pk=None):
        """
        GET /api/venues/{id}/verification/ — Get verification status (owner/admin only)
        Response: { verified, rejection_reason, submitted_at }
        
        POST /api/venues/{id}/verification/ — Submit/update verification documents (owner only)
        Files: citizenship_front, citizenship_back, pan_card, business_registration
        """
        venue = self.get_object()
        
        # Check permissions
        if not (venue.owner == request.user or request.user.is_staff):
            return Response(
                {'error': 'Only venue owner or admin can access verification'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            try:
                verification = VenueVerification.objects.get(venue=venue)
                return Response({
                    'id': str(verification.id),
                    'venue': str(verification.venue.id),
                    'verified': verification.verified,
                    'rejection_reason': verification.rejection_reason,
                    'verified_at':verification.verified_at.isoformat() if verification.verified_at else None,
                    'submitted_at': verification.created_at.isoformat() if verification.created_at else None
                })
            except VenueVerification.DoesNotExist:
                return Response(
                    {'detail': 'Verification not submitted yet'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        elif request.method == 'POST':
            # Only venue owner can submit verification documents
            if venue.owner != request.user:
                return Response(
                    {'error': 'Only venue owner can submit verification documents'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check required files
            required_files = ['citizenship_front', 'citizenship_back', 'pan_card', 'business_registration']
            for file_field in required_files:
                if file_field not in request.FILES:
                    return Response(
                        {'error': f'{file_field} is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            verification, created = VenueVerification.objects.update_or_create(
                venue=venue,
                defaults={
                    # Documents
                    'citizenship_front': request.FILES['citizenship_front'],
                    'citizenship_back': request.FILES['citizenship_back'],
                    'pan_card': request.FILES['pan_card'],
                    'business_registration': request.FILES['business_registration'],
                    # Reset verification state back to pending
                    'verified': False,
                    'rejection_reason': "",
                    'verified_at': None,
                }
            )

            return Response({
                'id': str(verification.id),
                'venue': str(verification.venue.id),
                'verified': verification.verified,
                'submitted_at': verification.created_at.isoformat(),
                'message': 'Verification documents submitted successfully' if created else 'Verification documents resubmitted, pending review'
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='create-full'
    )
    def create_full(self, request):
        """
        POST /api/venues/create-full/
        Single atomic endpoint: creates venue + turfs + images together.
        If anything fails, everything is rolled back.

        multipart/form-data fields:
            venue_name, venue_location, venue_description, venue_cover (file)
            turfs         — JSON string: [{"name":..., "sport":..., "price_per_hour":...}, ...]
            turf_images_0 — files for turf index 0
            turf_images_1 — files for turf index 1
            ...
        """
        venue = None
        try:
            with transaction.atomic():
                venue = self._atomic_create_venue(request)
                turfs = self._atomic_create_turfs(request, venue)
                self._atomic_attach_images(request.FILES, turfs)

            return Response(
                {"id": str(venue.id)},
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # DB already rolled back by atomic()
            # Manually clean up any files written to disk
            if venue:
                self._cleanup_venue_files(venue.id)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # ── private helpers ───────────────────────────────────────────────

    def _atomic_create_venue(self, request):
        import json
        
        # Extract amenities from JSON string
        amenities_str = request.data.get('venue_amenities', '{}')
        try:
            amenities = json.loads(amenities_str)
        except json.JSONDecodeError:
            amenities = {}
        
        data = {
            'name': request.data.get('venue_name'),
            'location': request.data.get('venue_location'),
            'description': request.data.get('venue_description'),
            'amenities': amenities,
        }
        serializer = VenueCreateUpdateSerializer(data=data, context={'request': request})
        if not serializer.is_valid():
            raise ValueError(serializer.errors)

        venue = serializer.save(owner=request.user)

        # Attach cover image if provided
        if 'venue_cover' in request.FILES:
            venue.cover_image = request.FILES['venue_cover']
            venue.save()

        return venue

    def _atomic_create_turfs(self, request, venue):
        import json
        raw = request.data.get('turfs')
        if not raw:
            raise ValueError("turfs field is required")

        try:
            turfs_data = json.loads(raw)   # parse JSON string from multipart
        except json.JSONDecodeError:
            raise ValueError("turfs must be valid JSON")

        if not isinstance(turfs_data, list) or len(turfs_data) == 0:
            raise ValueError("At least one turf is required")

        turfs = []
        for turf_data in turfs_data:
            serializer = TurfCreateUpdateSerializer(
                data={**turf_data, 'venue': venue.id},
                context={'request': request}
            )
            if not serializer.is_valid():
                raise ValueError(f"Turf error: {serializer.errors}")
            turf = serializer.save()
            turfs.append(turf)

        return turfs

    def _atomic_attach_images(self, files, turfs):
        for index, turf in enumerate(turfs):
            key = f'turf_images_{index}'
            images = files.getlist(key)

            if not images:
                raise ValueError(f"Images are required for turf at index {index}")

            if len(images) > 5:
                raise ValueError(f"Max 5 images allowed for turf at index {index}")

            for order, img in enumerate(images):
                TurfImage.objects.create(turf=turf, image=img, order=order)

    def _cleanup_venue_files(self, venue_id):
        """Remove all files written to disk for this venue"""
        venue_dir = os.path.join('media', 'venues', str(venue_id))
        if os.path.exists(venue_dir):
            shutil.rmtree(venue_dir)


class TurfViewSet(viewsets.ModelViewSet):
    """
    API for Turfs:
    - GET /api/turfs/ — List turfs (with filters: sport, location, min_rating)
    - POST /api/turfs/ — Create turf (owner only)
    - GET /api/turfs/{id}/ — Turf detail with images and reviews
    - PATCH /api/turfs/{id}/ — Update turf (owner only)
    - DELETE /api/turfs/{id}/ — Soft-delete (owner only)
    """
    queryset = Turf.objects.filter(deleted_at__isnull=True)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sport', 'status']
    search_fields = ['name', 'description', 'venue__location']
    ordering_fields = ['price_per_hour', 'avg_rating', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TurfDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TurfCreateUpdateSerializer
        return TurfListSerializer

    def get_queryset(self):
        """
        Show only non-deleted turfs.
        For app: only show active turfs.
        """
        queryset = Turf.objects.filter(deleted_at__isnull=True).select_related('venue')
        
        # For list view, filter only active turfs (unless admin)
        if self.action == 'list':
            queryset = queryset.filter(status='active')

        # Filter by min_rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(avg_rating__gte=Decimal(min_rating))

        # Filter by location (venue location)
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(venue__location__icontains=location)

        return queryset

    def perform_create(self, serializer):
        """Validate owner permission"""
        venue = serializer.validated_data.get('venue')
        if venue.owner != self.request.user:
            return Response(
                {'error': 'You can only create turfs in your own venues'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Soft delete: set deleted_at instead of hard delete"""
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=True, methods=['post'], url_path='confirm-delete')
    def confirm_delete(self, request, pk=None):
        turf = self.get_object()
        verify_owner_password_or_403(request, turf.venue.owner)
        turf.deleted_at = timezone.now()
        turf.save()
        return Response({'message': 'Truf deleted successfully.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get available time slots for a turf.
        Query params: ?date=YYYY-MM-DD
        Returns: [{"start": "06:00", "end": "07:00", "available": true}, ...]
        """
        turf = self.get_object()
        date_str = request.query_params.get('date')

        if not date_str:
            return Response(
                {'error': 'date query parameter required (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format (use YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate 1-hour slots between opening and closing time
        opening = datetime.combine(date, turf.opening_time)
        closing = datetime.combine(date, turf.closing_time)

        slots = []
        current = opening
        while current < closing:
            next_slot = current + timedelta(hours=1)
            if next_slot > closing:
                break

            # TODO: Check against actual bookings when Booking model exists
            available = True  # placeholder

            slots.append({
                'start': current.strftime('%H:%M'),
                'end': next_slot.strftime('%H:%M'),
                'available': available
            })
            current = next_slot

        return Response(slots)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def images(self, request, pk=None):
        """
        GET /api/turfs/{id}/images/ — List all images
        POST /api/turfs/{id}/images/ — Upload images (multipart, max 5)
        """
        turf = self.get_object()

        if request.method == 'GET':
            images = turf.images.all()
            serializer = TurfImageSerializer(images, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            # Check ownership
            if turf.venue.owner != request.user:
                return Response(
                    {'error': 'Only owner can upload images'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check max 5 images limit
            image_count = turf.images.count()
            if image_count >= 5:
                return Response(
                    {'error': 'Maximum 5 images allowed per turf'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            files = request.FILES.getlist('images')
            if not files:
                return Response(
                    {'error': 'No images provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Limit to remaining slots
            files = files[:5 - image_count]
            created_images = []

            for file in files:
                image = TurfImage.objects.create(
                    turf=turf,
                    image=file,
                    order=image_count + created_images.__len__()
                )
                created_images.append(image)

            serializer = TurfImageSerializer(created_images, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='img_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the turf image'
            )
        ]
    )
    @action(
        detail=True,
        methods=['patch', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='images/(?P<img_id>[^/.]+)'
    )
    def image_detail(self, request, pk=None, img_id=None):
        """
        PATCH /api/turfs/{id}/images/{img_id}/ — Update image (set cover, reorder)
        DELETE /api/turfs/{id}/images/{img_id}/ — Delete image
        """
        turf = self.get_object()

        try:
            image = TurfImage.objects.get(id=img_id, turf=turf)
        except TurfImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check ownership
        if turf.venue.owner != request.user:
            return Response(
                {'error': 'Only owner can modify images'},
                status=status.HTTP_403_FORBIDDEN
            )

        if request.method == 'PATCH':
            order = request.data.get('order')
            new_image = request.FILES.get('image')

            #replace image
            if new_image:
                if image.image:
                    image.image.delete(save=False)
                image.image = new_image
                
            if order is not None:
                image.order = order

            image.save()
            serializer = TurfImageSerializer(image)
            return Response(serializer.data)

        elif request.method == 'DELETE':
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get', 'post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def reviews(self, request, pk=None):
        """
        GET /api/turfs/{id}/reviews/ — List reviews
        POST /api/turfs/{id}/reviews/ — Submit review (authenticated)
        """
        turf = self.get_object()

        if request.method == 'GET':
            reviews = turf.reviews.all()
            serializer = TurfReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            if not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required to review'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            serializer = TurfReviewSerializer(
                data=request.data,
                context={'request': request, 'turf': turf}
            )
            if serializer.is_valid():
                review = serializer.save()
                # TODO: Update turf.avg_rating via signal
                return Response(
                    TurfReviewSerializer(review).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='rev_id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='UUID of the turf review'
            )
        ]
    )
    @action(
        detail=True,
        methods=['patch', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='reviews/(?P<rev_id>[^/.]+)'
    )
    def review_detail(self, request, pk=None, rev_id=None):
        """
        PATCH /api/turfs/{id}/reviews/{rev_id}/ — Edit own review
        DELETE /api/turfs/{id}/reviews/{rev_id}/ — Delete own review
        """
        turf = self.get_object()

        try:
            review = TurfReview.objects.get(id=rev_id, turf=turf)
        except TurfReview.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check ownership (client can edit/delete own, admin can delete any)
        if request.method == 'DELETE':
            if review.client != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'You can only delete your own reviews'},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:  # PATCH
            if review.client != request.user:
                return Response(
                    {'error': 'You can only edit your own reviews'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if request.method == 'PATCH':
            serializer = TurfReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                review = serializer.save()
                # TODO: Update turf.avg_rating via signal
                return Response(TurfReviewSerializer(review).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            review.delete()
            # TODO: Update turf.avg_rating via signal
            return Response(status=status.HTTP_204_NO_CONTENT)