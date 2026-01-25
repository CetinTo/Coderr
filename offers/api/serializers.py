from django.db.models import Min
from rest_framework import serializers
from ..models import Offer, OfferDetail


class OfferDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferDetail
        fields = ['id', 'offer_type', 'title', 'price', 'delivery_time_in_days', 
                 'revisions', 'features']
        read_only_fields = ['id']
    
    def validate_price(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Price must be a number, not a string.")
        return value
    
    def validate_delivery_time_in_days(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Delivery time must be an integer, not a string.")
        return value
    
    def validate_revisions(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Revisions must be an integer, not a string.")
        return value
    
    def validate_title(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Ensures no null values are returned for numeric fields (converts None to 0).
        This is a safety measure, though the model fields should never be None.
        """
        data = super().to_representation(instance)
        # Convert None to 0 for numeric fields (should never happen, but safety check)
        if data.get('price') is None:
            data['price'] = 0
        if data.get('delivery_time_in_days') is None:
            data['delivery_time_in_days'] = 0
        if data.get('revisions') is None:
            data['revisions'] = 0
        return data


class OfferListSerializer(serializers.ModelSerializer):
    """
    Serializer for Offer list (GET /api/offers/).
    
    Uses ModelSerializer which automatically includes all model fields.
    Calculated fields (min_price, min_delivery_time) come from annotate() in get_queryset(),
    computed directly in the database query for optimal performance.
    Uses to_representation() to format the response structure (user instead of creator, etc.).
    """
    details = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False)
    min_delivery_time = serializers.IntegerField(read_only=True)
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Offer
        fields = ['id', 'creator', 'title', 'image', 'description', 'created_at', 
                 'updated_at', 'details', 'min_price', 'min_delivery_time', 'user_details']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_details(self, obj):
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
    
    def get_user_details(self, obj):
        creator = obj.creator
        return {
            'first_name': creator.first_name or '',
            'last_name': creator.last_name or '',
            'username': creator.username or ''
        }
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Converts the response structure to match frontend expectations:
        - Renames 'creator' to 'user' (creator.id)
        - Converts min_price from Decimal to float for JSON compatibility
        """
        data = super().to_representation(instance)
        # Rename creator to user (flatten structure - use creator.id)
        if 'creator' in data:
            # Extract creator.id - handle both dict and int formats
            if isinstance(data['creator'], dict) and 'id' in data['creator']:
                data['user'] = data['creator']['id']
            elif isinstance(data['creator'], int):
                data['user'] = data['creator']
            else:
                # Fallback: get id directly from instance
                data['user'] = instance.creator.id if instance.creator else None
            del data['creator']
        # Convert Decimal to float for JSON compatibility
        if data.get('min_price') is not None:
            data['min_price'] = float(data['min_price'])
        return data


class OfferCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for Offer creation (POST /api/offers/).
    
    Handles creation of Offer with nested OfferDetail objects.
    The model fields (title, description, image) are automatically included from the model.
    Only the nested 'details' field is explicitly defined as it requires special handling.
    """
    details = OfferDetailSerializer(many=True, required=True)
    
    class Meta:
        model = Offer
        fields = ['title', 'description', 'image', 'details']
    
    def validate_title(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip() if value else value
    
    def validate_description(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value.strip() if value else value
    
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
    


class OfferDetailResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for Offer Detail Response (GET /api/offers/{id}/).
    
    Uses ModelSerializer which automatically includes all model fields.
    Calculated fields (min_price, min_delivery_time) come from annotate() in get_queryset(),
    computed directly in the database query for optimal performance.
    Uses to_representation() to format the response structure (user instead of creator).
    """
    details = serializers.SerializerMethodField()
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, coerce_to_string=False)
    min_delivery_time = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Offer
        fields = ['id', 'creator', 'title', 'image', 'description', 'created_at', 
                 'updated_at', 'details', 'min_price', 'min_delivery_time']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_details(self, obj):
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
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Converts the response structure to match frontend expectations:
        - Renames 'creator' to 'user' (creator.id)
        - Converts min_price from Decimal to float for JSON compatibility
        """
        data = super().to_representation(instance)
        # Rename creator to user (flatten structure - use creator.id)
        if 'creator' in data:
            # Extract creator.id - handle both dict and int formats
            if isinstance(data['creator'], dict) and 'id' in data['creator']:
                data['user'] = data['creator']['id']
            elif isinstance(data['creator'], int):
                data['user'] = data['creator']
            else:
                # Fallback: get id directly from instance
                data['user'] = instance.creator.id if instance.creator else None
            del data['creator']
        # Convert Decimal to float for JSON compatibility
        if data.get('min_price') is not None:
            data['min_price'] = float(data['min_price'])
        return data


class OfferUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Offer Update (PATCH /api/offers/{id}/).
    
    Handles partial updates of Offer with optional nested OfferDetail updates.
    The model fields (title, description, image) are automatically included from the model.
    Only the nested 'details' field is explicitly defined as it requires special handling.
    All fields are optional for PATCH requests.
    """
    details = OfferDetailSerializer(many=True, required=False)
    title = serializers.CharField(required=False, allow_blank=False)
    description = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Offer
        fields = ['title', 'description', 'image', 'details']
    
    
    def validate_details(self, value):
        """Validate details array."""
        if value is None:
            return value
        
        if not isinstance(value, list):
            raise serializers.ValidationError("Details must be a list.")
        
        for detail in value:
            if not isinstance(detail, dict):
                raise serializers.ValidationError("Each detail must be an object.")
            
            # Validate offer_type
            offer_type = detail.get('offer_type')
            if offer_type and offer_type not in ['basic', 'standard', 'premium']:
                raise serializers.ValidationError(
                    f"Invalid offer_type '{offer_type}'. Must be 'basic', 'standard', or 'premium'."
                )
            
            # Validate numeric fields - must be numbers, not strings
            if 'price' in detail:
                price = detail['price']
                if isinstance(price, str):
                    raise serializers.ValidationError("Price must be a number, not a string.")
                if price is not None and price < 0:
                    raise serializers.ValidationError("Price cannot be negative.")
            
            if 'delivery_time_in_days' in detail:
                delivery_time = detail['delivery_time_in_days']
                if isinstance(delivery_time, str):
                    raise serializers.ValidationError("Delivery time must be an integer, not a string.")
                if delivery_time is not None and delivery_time < 0:
                    raise serializers.ValidationError("Delivery time cannot be negative.")
            
            if 'revisions' in detail:
                revisions = detail['revisions']
                if isinstance(revisions, str):
                    raise serializers.ValidationError("Revisions must be an integer, not a string.")
                if revisions is not None and revisions < -1:
                    raise serializers.ValidationError("Revisions must be -1 (unlimited) or positive.")
            
            # Validate title if present
            if 'title' in detail:
                title = detail.get('title')
                if title and not isinstance(title, str):
                    raise serializers.ValidationError("Title must be a string.")
                if title and not title.strip():
                    raise serializers.ValidationError("Title cannot be empty.")
        
        return value
    
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
    """
    Base Serializer for Offer (default serializer).
    
    Uses ModelSerializer which automatically includes all model fields.
    Used as fallback when no specific serializer is needed for an action.
    
    Note: Most actions use specialized serializers (OfferListSerializer, OfferCreateSerializer, etc.)
    instead of this base serializer.
    """
    details = OfferDetailSerializer(many=True, required=False, read_only=True)
    
    class Meta:
        model = Offer
        fields = ['id', 'creator', 'title', 'description', 'image', 'details', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
