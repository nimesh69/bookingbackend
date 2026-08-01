from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from drf_spectacular.utils import extend_schema_field
from .models import Venue, Turf, TurfImage, TurfReview, VenueVerification




class TurfImageSerializer(serializers.ModelSerializer):
    """Serializer for turf images"""
    class Meta:
        model = TurfImage
        fields = ['id', 'image', 'order', 'created_at']
        read_only_fields = ['id', 'created_at']


class TurfReviewSerializer(serializers.ModelSerializer):
    """Serializer for turf reviews"""
    client_name = serializers.CharField(source='client.email', read_only=True)

    class Meta:
        model = TurfReview
        fields = ['id', 'client', 'client_name', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'client', 'client_name', 'created_at']

    def create(self, validated_data):
        """Enforce unique_together constraint"""
        turf = self.context['turf']
        client = self.context['request'].user
        
        existing_review = TurfReview.objects.filter(
            turf=turf, client=client
        ).exists()
        
        if existing_review:
            raise serializers.ValidationError(
                "You have already reviewed this turf."
            )
        
        return TurfReview.objects.create(
            turf=turf,
            client=client,
            **validated_data
        )


class TurfDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for turf with nested images and reviews"""
    images = TurfImageSerializer(many=True, read_only=True)
    # reviews = TurfReviewSerializer(many=True, read_only=True)
    reviews_count = serializers.SerializerMethodField()
    venue_name = serializers.CharField(source='venue.name', read_only=True)

    class Meta:
        model = Turf
        fields = [
            'id', 'venue', 'venue_name', 'sport', 'name', 'description',
            'price_per_hour', 'max_players', 'court_count', 'opening_time',
            'closing_time', 'avg_rating', 'status', 'images',
            'reviews_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'avg_rating', 'created_at', 'updated_at']

    @extend_schema_field(serializers.IntegerField())
    def get_reviews_count(self, obj) -> int:
        return obj.reviews.count()


class TurfListSerializer(serializers.ModelSerializer):
    """List serializer for turfs (without nested images/reviews for performance)"""
    cover_image = serializers.SerializerMethodField()
    venue_name = serializers.CharField(source='venue.name', read_only=True)

    class Meta:
        model = Turf
        fields = [
            'id', 'venue', 'venue_name', 'sport', 'name', 'price_per_hour','description',
            'max_players', 'avg_rating', 'status', 'cover_image', 'created_at','opening_time','closing_time'
        ]
        read_only_fields = ['id', 'created_at']

    @extend_schema_field(TurfImageSerializer)
    def get_cover_image(self, obj) -> dict:
        # First image is the cover image (ordered by order field)
        cover = obj.images.first()
        return TurfImageSerializer(cover).data if cover else None


class TurfCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating turfs"""
    class Meta:
        model = Turf
        fields = [
            'id', 'venue', 'sport', 'name', 'description', 'price_per_hour',
            'max_players', 'court_count', 'opening_time', 'closing_time', 'avg_rating',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'avg_rating', 'created_at', 'updated_at']


class VenueDetailSerializer(serializers.ModelSerializer):
    turfs = serializers.SerializerMethodField()
    turfs_count = serializers.SerializerMethodField()
    cover_image = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = Venue
        fields = [
            'id', 'owner', 'name', 'location', 'amenities', 'status',
            'cover_image', 'turfs', 'turfs_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    @extend_schema_field(TurfListSerializer(many=True))
    def get_turfs(self, obj):
        active_turfs = obj.turfs.filter(deleted_at__isnull=True)
        return TurfListSerializer(active_turfs, many=True, context=self.context).data

    @extend_schema_field(serializers.IntegerField())
    def get_turfs_count(self, obj) -> int:
        return obj.turfs.filter(deleted_at__isnull=True).count()


class VenueListSerializer(serializers.ModelSerializer):
    """List serializer for venues"""
    turfs_count = serializers.SerializerMethodField()
    cover_image = serializers.ImageField(read_only=True)
    venue_sports = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Venue
        fields = ['id', 'name', 'location', 'status', 'cover_image', 'turfs_count', 'created_at','owner','amenities','venue_sports']
        read_only_fields = ['id', 'created_at']

    @extend_schema_field(serializers.IntegerField())
    def get_turfs_count(self, obj) -> int:
        return obj.turfs.filter(deleted_at__isnull=True).count()
    
    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_venue_sports(self, obj):
        return list(obj.turfs.filter(deleted_at__isnull=True).order_by().values_list("sport", flat=True).distinct())

class VenueVerificationSerializer(serializers.ModelSerializer):
    """Serializer for venue verification - for admin panel only"""
    class Meta:
        model = VenueVerification
        fields = [
            'id',
            'citizenship_front',
            'citizenship_back',
            'pan_card',
            'business_registration',
            'verified',
            'verified_at',
            'rejection_reason',
        ]
        read_only_fields = [
            'verified',
            'verified_at',
            'rejection_reason',
        ]


class VenueVerificationStatusSerializer(serializers.ModelSerializer):
    """Serializer for verification status - read-only, no file URLs exposed"""
    class Meta:
        model = VenueVerification
        fields = [
            'verified',
            'rejection_reason',
            'verified_at',
            'created_at',
        ]
        read_only_fields = [
            'verified',
            'rejection_reason',
            'verified_at',
            'created_at',
        ]

class VenueCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating venues"""
    class Meta:
        model = Venue
        fields = ['id', 'name', 'location', 'amenities','cover_image', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
