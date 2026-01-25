from rest_framework import serializers
from offers.api.serializers import OfferDetailSerializer, OfferSerializer
from ..models import Order


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for Order list (GET /api/orders/)."""
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'offer', 'offer_detail', 'status', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
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
    offer = OfferSerializer(read_only=True)
    offer_detail = OfferDetailSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'offer', 'offer_detail', 'status', 
                 'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    


class OrderCreateSerializer(serializers.Serializer):
    offer_detail_id = serializers.IntegerField(required=True)
    
    def validate_offer_detail_id(self, value):
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
    class Meta:
        model = Order
        fields = ['status']
    
    
    def update(self, instance, validated_data):
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
