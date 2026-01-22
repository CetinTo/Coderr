from rest_framework import serializers
from offers.api.serializers import OfferDetailSerializer, OfferSerializer
from ..models import Order


class OrderListSerializer(serializers.ModelSerializer):
    """
    Serializer for Order list (GET /api/orders/).
    
    Uses ModelSerializer which automatically includes all model fields.
    Uses to_representation() to format the response structure with flattened fields
    from related objects (offer_detail fields, business_user from offer.creator).
    """
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'offer', 'offer_detail', 'status', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Flattens the response structure to match frontend expectations:
        - customer_user: customer.id
        - business_user: offer.creator.id (if offer exists)
        - title, revisions, delivery_time_in_days, price, features, offer_type: from offer_detail
        """
        data = super().to_representation(instance)
        
        # Flatten customer to customer_user
        if 'customer' in data:
            data['customer_user'] = data['customer']
            del data['customer']
        
        # Extract business_user from offer.creator (if offer exists)
        if instance.offer and instance.offer.creator:
            data['business_user'] = instance.offer.creator.id
        else:
            data['business_user'] = None
        
        # Extract fields from offer_detail (if exists)
        if instance.offer_detail:
            data['title'] = instance.offer_detail.title
            data['revisions'] = instance.offer_detail.revisions
            data['delivery_time_in_days'] = instance.offer_detail.delivery_time_in_days
            data['price'] = float(instance.offer_detail.price) if instance.offer_detail.price else None
            data['features'] = instance.offer_detail.features
            data['offer_type'] = instance.offer_detail.offer_type
        else:
            data['title'] = None
            data['revisions'] = None
            data['delivery_time_in_days'] = None
            data['price'] = None
            data['features'] = None
            data['offer_type'] = None
        
        # Remove nested objects (offer, offer_detail) as we've flattened their fields
        if 'offer' in data:
            del data['offer']
        if 'offer_detail' in data:
            del data['offer_detail']
        
        return data


class OrderSerializer(serializers.ModelSerializer):
    """
    Base Serializer for Order.
    
    Uses ModelSerializer which automatically includes all model fields.
    Nested serializers for offer and offer_detail provide full related object data.
    """
    offer = OfferSerializer(read_only=True)
    offer_detail = OfferDetailSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'offer', 'offer_detail', 'status', 
                 'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating an Order"""
    offer_detail_id = serializers.IntegerField(required=True)
    
    def validate_offer_detail_id(self, value):
        """Validate that the OfferDetail exists and its Offer is not deleted"""
        if isinstance(value, str):
            raise serializers.ValidationError("Offer detail ID must be an integer, not a string.")
        from offers.models import OfferDetail
        try:
            offer_detail = OfferDetail.objects.get(pk=value)
            # Check if the offer still exists (not deleted)
            if not offer_detail.offer:
                raise serializers.ValidationError("Cannot create order for a deleted offer.")
            return value
        except OfferDetail.DoesNotExist:
            raise serializers.ValidationError("The specified offer detail was not found.")
    
    def create(self, validated_data):
        """Create a new order"""
        from offers.models import OfferDetail
        offer_detail_id = validated_data['offer_detail_id']
        offer_detail = OfferDetail.objects.get(pk=offer_detail_id)
        offer = offer_detail.offer
        
        # Double check that offer exists (not deleted)
        if not offer:
            raise serializers.ValidationError("Cannot create order for a deleted offer.")
        
        customer = self.context['request'].user
        
        order = Order.objects.create(
            customer=customer,
            offer=offer,
            offer_detail=offer_detail,
            status='pending'
        )
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an Order (status only)"""
    class Meta:
        model = Order
        fields = ['status']
    
    
    def update(self, instance, validated_data):
        """Update the status and set completed_at if necessary"""
        from django.utils import timezone
        
        status = validated_data.get('status', instance.status)
        instance.status = status
        
        # Set completed_at when status is set to 'completed'
        if status == 'completed' and not instance.completed_at:
            instance.completed_at = timezone.now()
        elif status != 'completed':
            instance.completed_at = None
        
        instance.save()
        return instance
