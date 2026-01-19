# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.db.models import Min
from rest_framework import serializers

# 3. Lokale Importe
from .models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    """Serializer for OfferDetail"""
    price = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
    delivery_time_in_days = serializers.IntegerField()
    revisions = serializers.IntegerField()
    
    class Meta:
        model = OfferDetail
        fields = ['id', 'offer_type', 'title', 'price', 'delivery_time_in_days', 
                 'revisions', 'features']
        read_only_fields = ['id']
    
    def validate_price(self, value):
        """Validate price."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    
    def validate_delivery_time_in_days(self, value):
        """Validate delivery time."""
        if value < 0:
            raise serializers.ValidationError("Delivery time cannot be negative.")
        return value
    
    def validate_revisions(self, value):
        """Validate revisions."""
        if value < -1:
            raise serializers.ValidationError("Revisions must be -1 (unlimited) or positive.")
        return value
    
    def validate_title(self, value):
        """Validate title."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def to_representation(self, instance):
        """Ensure no null values are returned"""
        data = super().to_representation(instance)
        # Convert None to 0 for numeric fields (should never happen)
        if data.get('price') is None:
            data['price'] = 0
        if data.get('delivery_time_in_days') is None:
            data['delivery_time_in_days'] = 0
        if data.get('revisions') is None:
            data['revisions'] = 0
        return data


class OfferListSerializer(serializers.ModelSerializer):
    """Serializer for Offer list with min_price, min_delivery_time and user_details"""
    user = serializers.IntegerField(source='creator.id', read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 
                 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_details(self, obj):
        """Returns full details with no null values"""
        details = obj.details.all()
        result = []
        for detail in details:
            detail_data = OfferDetailSerializer(detail).data
            # Ensure no null values
            if detail_data.get('price') is None:
                detail_data['price'] = 0
            if detail_data.get('delivery_time_in_days') is None:
                detail_data['delivery_time_in_days'] = 0
            if detail_data.get('revisions') is None:
                detail_data['revisions'] = 0
            result.append(detail_data)
        return result
    
    def get_min_price(self, obj):
        """Calculates the minimum price of all details"""
        min_price = obj.details.aggregate(Min('price'))['price__min']
        return float(min_price) if min_price is not None else None
    
    def get_min_delivery_time(self, obj):
        """Calculates the shortest delivery time of all details"""
        min_delivery = obj.details.aggregate(Min('delivery_time_in_days'))['delivery_time_in_days__min']
        return min_delivery if min_delivery is not None else None
    
    def get_user_details(self, obj):
        """Returns user details"""
        creator = obj.creator
        return {
            'first_name': creator.first_name or '',
            'last_name': creator.last_name or '',
            'username': creator.username or ''
        }


class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for Offer creation"""
    details = OfferDetailSerializer(many=True, required=True)
    
    class Meta:
        model = Offer
        fields = ['title', 'description', 'image', 'details']
    
    def validate_title(self, value):
        """Validate title."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def validate_description(self, value):
        """Validate description."""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()
    
    def validate_details(self, value):
        """Validate that exactly 3 details are present"""
        if len(value) != 3:
            raise serializers.ValidationError("An offer must contain exactly 3 details.")
        
        # Check that all three offer_types are present
        offer_types = [detail.get('offer_type') for detail in value]
        required_types = ['basic', 'standard', 'premium']
        
        if set(offer_types) != set(required_types):
            raise serializers.ValidationError(
                "The details must contain the offer_types 'basic', 'standard' and 'premium'."
            )
        
        # Convert null values to 0 for numeric fields
        for detail in value:
            if detail.get('price') is None:
                detail['price'] = 0
            if detail.get('delivery_time_in_days') is None:
                detail['delivery_time_in_days'] = 0
            if detail.get('revisions') is None:
                detail['revisions'] = 0
        
        return value
    
    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        offer = Offer.objects.create(**validated_data)
        
        # Create OfferDetails
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        
        return offer


class OfferCreateResponseSerializer(serializers.ModelSerializer):
    """Serializer for Offer Create Response"""
    details = OfferDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        """Ensure all details have no null values."""
        data = super().to_representation(instance)
        # Ensure all details are properly serialized with OfferDetailSerializer
        if 'details' in data and isinstance(data['details'], list):
            for detail in data['details']:
                if detail.get('price') is None:
                    detail['price'] = 0
                if detail.get('delivery_time_in_days') is None:
                    detail['delivery_time_in_days'] = 0
                if detail.get('revisions') is None:
                    detail['revisions'] = 0
        return data


class OfferDetailResponseSerializer(serializers.ModelSerializer):
    """Serializer for Offer Detail Response (GET /api/offers/{id}/)"""
    user = serializers.IntegerField(source='creator.id', read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = ['id', 'user', 'title', 'image', 'description', 'created_at', 
                 'updated_at', 'details', 'min_price', 'min_delivery_time']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_details(self, obj):
        """Returns id and full URL for each detail"""
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/') if request else 'http://127.0.0.1:8000/'
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        details = obj.details.all()
        return [
            {
                'id': detail.id,
                'url': f"{base_url}/api/offerdetails/{detail.id}/"
            }
            for detail in details
        ]
    
    def get_min_price(self, obj):
        """Calculates the minimum price of all details"""
        min_price = obj.details.aggregate(Min('price'))['price__min']
        return float(min_price) if min_price is not None else None
    
    def get_min_delivery_time(self, obj):
        """Calculates the shortest delivery time of all details"""
        min_delivery = obj.details.aggregate(Min('delivery_time_in_days'))['delivery_time_in_days__min']
        return min_delivery if min_delivery is not None else None


class OfferUpdateSerializer(serializers.ModelSerializer):
    """Serializer for Offer Update (PATCH)"""
    details = OfferDetailSerializer(many=True, required=False)
    
    class Meta:
        model = Offer
        fields = ['title', 'description', 'image', 'details']
    
    def validate_title(self, value):
        """Validate title."""
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value
    
    def validate_description(self, value):
        """Validate description."""
        if value and not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip() if value else value
    
    def _update_offer_fields(self, instance, validated_data):
        """Update offer fields excluding details."""
        for attr, value in validated_data.items():
            if attr != 'details':
                setattr(instance, attr, value)
        instance.save()
    
    def _update_offer_detail(self, instance, detail_data):
        """Update a single offer detail."""
        offer_type = detail_data.get('offer_type')
        if not offer_type:
            return
        
        # Convert null values to 0 for numeric fields
        if detail_data.get('price') is None:
            detail_data['price'] = 0
        if detail_data.get('delivery_time_in_days') is None:
            detail_data['delivery_time_in_days'] = 0
        if detail_data.get('revisions') is None:
            detail_data['revisions'] = 0
        
        try:
            detail = instance.details.get(offer_type=offer_type)
            for key, value in detail_data.items():
                if key != 'offer_type':
                    setattr(detail, key, value)
            detail.save()
        except OfferDetail.DoesNotExist:
            OfferDetail.objects.create(offer=instance, **detail_data)
    
    def update(self, instance, validated_data):
        """Update offer and its details."""
        self._update_offer_fields(instance, validated_data)
        
        details_data = validated_data.get('details', None)
        if details_data is not None:
            for detail_data in details_data:
                self._update_offer_detail(instance, detail_data)
        
        return instance


class OfferSerializer(serializers.ModelSerializer):
    """Serializer for Offer (complete)"""
    details = OfferDetailSerializer(many=True, required=False)
    creator_id = serializers.IntegerField(source='creator.id', read_only=True)
    creator_username = serializers.CharField(source='creator.username', read_only=True)
    
    class Meta:
        model = Offer
        fields = ['id', 'creator', 'creator_id', 'creator_username', 'title', 
                 'description', 'image', 'details', 'created_at', 'updated_at']
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
    
    def validate_title(self, value):
        """Validate title."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def validate_description(self, value):
        """Validate description."""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip()
    
    def create(self, validated_data):
        details_data = validated_data.pop('details', [])
        offer = Offer.objects.create(**validated_data)
        
        # Create OfferDetails
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        
        return offer
    
    def _update_offer_fields(self, instance, validated_data):
        """Update offer fields."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
    
    def _replace_offer_details(self, instance, details_data):
        """Replace all offer details with new ones."""
        instance.details.all().delete()
        for detail_data in details_data:
            OfferDetail.objects.create(offer=instance, **detail_data)
    
    def update(self, instance, validated_data):
        """Update offer and replace details."""
        details_data = validated_data.pop('details', None)
        self._update_offer_fields(instance, validated_data)
        
        if details_data is not None:
            self._replace_offer_details(instance, details_data)
        
        return instance

