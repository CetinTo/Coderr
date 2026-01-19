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
    business_user = serializers.IntegerField(source='offer.creator.id', read_only=True)
    title = serializers.CharField(source='offer_detail.title', read_only=True)
    revisions = serializers.IntegerField(source='offer_detail.revisions', read_only=True)
    delivery_time_in_days = serializers.IntegerField(source='offer_detail.delivery_time_in_days', read_only=True)
    price = serializers.DecimalField(source='offer_detail.price', max_digits=10, decimal_places=2, read_only=True)
    features = serializers.JSONField(source='offer_detail.features', read_only=True)
    offer_type = serializers.CharField(source='offer_detail.offer_type', read_only=True)
    
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
        """Validate that the OfferDetail exists"""
        from offers.models import OfferDetail
        try:
            offer_detail = OfferDetail.objects.get(pk=value)
            return value
        except OfferDetail.DoesNotExist:
            raise serializers.ValidationError("The specified offer detail was not found.")
    
    def create(self, validated_data):
        """Create a new order"""
        from offers.models import OfferDetail
        offer_detail_id = validated_data['offer_detail_id']
        offer_detail = OfferDetail.objects.get(pk=offer_detail_id)
        offer = offer_detail.offer
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

