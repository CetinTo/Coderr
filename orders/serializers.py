# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import serializers

# 3. Lokale Importe
from offers.serializers import OfferDetailSerializer, OfferSerializer
from .models import Order


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for Order list (GET /api/orders/)"""
    customer_user = serializers.IntegerField(source='customer.id', read_only=True)
    business_user = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    revisions = serializers.SerializerMethodField()
    delivery_time_in_days = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    offer_type = serializers.SerializerMethodField()
    
    def get_business_user(self, obj):
        """Get business user ID, handling deleted offers."""
        return obj.offer.creator.id if obj.offer and obj.offer.creator else None
    
    def get_title(self, obj):
        """Get title, handling deleted offer details."""
        return obj.offer_detail.title if obj.offer_detail else None
    
    def get_revisions(self, obj):
        """Get revisions, handling deleted offer details."""
        return obj.offer_detail.revisions if obj.offer_detail else None
    
    def get_delivery_time_in_days(self, obj):
        """Get delivery time, handling deleted offer details."""
        return obj.offer_detail.delivery_time_in_days if obj.offer_detail else None
    
    def get_price(self, obj):
        """Get price, handling deleted offer details."""
        return float(obj.offer_detail.price) if obj.offer_detail and obj.offer_detail.price else None
    
    def get_features(self, obj):
        """Get features, handling deleted offer details."""
        return obj.offer_detail.features if obj.offer_detail else None
    
    def get_offer_type(self, obj):
        """Get offer type, handling deleted offer details."""
        return obj.offer_detail.offer_type if obj.offer_detail else None
    
    class Meta:
        model = Order
        fields = ['id', 'customer_user', 'business_user', 'title', 'revisions', 
                 'delivery_time_in_days', 'price', 'features', 'offer_type', 
                 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order"""
    offer = OfferSerializer(read_only=True)
    offer_detail = OfferDetailSerializer(read_only=True)
    customer_id = serializers.IntegerField(source='customer.id', read_only=True)
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_id', 'customer_username', 'offer', 
                 'offer_detail', 'status', 'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_status(self, value):
        """Validate status."""
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Allowed values: {', '.join(valid_statuses)}"
            )
        return value


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating an Order"""
    offer_detail_id = serializers.IntegerField(required=True)
    
    def validate_offer_detail_id(self, value):
        """Validate that the OfferDetail exists and its Offer is not deleted"""
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
    
    def validate_status(self, value):
        """Validate the status"""
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status. Allowed values: {', '.join(valid_statuses)}"
            )
        return value
    
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

