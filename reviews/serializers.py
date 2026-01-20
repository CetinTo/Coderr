# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import serializers

# 3. Lokale Importe
from .models import Review


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for Review list (GET /api/reviews/)"""
    business_user = serializers.IntegerField(source='business.id', read_only=True)
    reviewer = serializers.IntegerField(source='customer.id', read_only=True)
    description = serializers.CharField(source='comment', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review"""
    customer_id = serializers.IntegerField(source='customer.id', read_only=True)
    customer_username = serializers.CharField(source='customer.username', read_only=True)
    business_id = serializers.IntegerField(source='business.id', read_only=True)
    business_username = serializers.CharField(source='business.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'customer', 'customer_id', 'customer_username', 'business', 
                 'business_id', 'business_username', 'order', 'rating', 'comment', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        """Validate rating."""
        if value < 1 or value > 5:
            raise serializers.ValidationError("The rating must be between 1 and 5.")
        return value


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating a Review"""
    business_user = serializers.IntegerField(required=True, write_only=True)
    rating = serializers.IntegerField(required=True)
    description = serializers.CharField(required=True, allow_blank=True)
    
    def validate_business_user(self, value):
        """Validate that the business user exists and is a business user"""
        from accounts_app.models import User
        try:
            user = User.objects.get(pk=value)
            if user.user_type != 'business':
                raise serializers.ValidationError("The specified user is not a business user.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("The specified business user was not found.")
    
    def validate_rating(self, value):
        """Validate that the rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("The rating must be between 1 and 5.")
        return value
    
    def validate(self, attrs):
        """Validate that the customer has not already reviewed this business user"""
        customer = self.context['request'].user
        business_user_id = attrs['business_user']
        
        # Check if a review already exists
        if Review.objects.filter(customer=customer, business_id=business_user_id).exists():
            raise serializers.ValidationError(
                "You have already submitted a review for this business user."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Create a new review"""
        from accounts_app.models import User
        business_user_id = validated_data.pop('business_user')
        description = validated_data.pop('description')
        rating = validated_data['rating']
        customer = self.context['request'].user
        
        business_user = User.objects.get(pk=business_user_id)
        
        review = Review.objects.create(
            customer=customer,
            business=business_user,
            rating=rating,
            comment=description
        )
        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a Review (rating and description only)"""
    description = serializers.CharField(source='comment', required=False, allow_blank=True)
    
    class Meta:
        model = Review
        fields = ['rating', 'description']
    
    def validate_rating(self, value):
        """Validate that the rating is between 1 and 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("The rating must be between 1 and 5.")
        return value
    
    def update(self, instance, validated_data):
        """Update only rating and description"""
        if 'comment' in validated_data:
            instance.comment = validated_data['comment']
        if 'rating' in validated_data:
            instance.rating = validated_data['rating']
        instance.save()
        return instance

