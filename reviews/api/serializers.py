from rest_framework import serializers
from ..models import Review


class ReviewListSerializer(serializers.ModelSerializer):
    """
    Serializer for Review list (GET /api/reviews/).
    
    Uses ModelSerializer which automatically includes all model fields.
    Uses to_representation() to format the response structure (business_user, reviewer, description).
    """
    
    class Meta:
        model = Review
        fields = ['id', 'customer', 'business', 'rating', 'comment', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Converts the response structure to match frontend expectations:
        - business_user: business.id
        - reviewer: customer.id
        - description: comment
        """
        data = super().to_representation(instance)
        
        # Flatten business to business_user
        if 'business' in data:
            data['business_user'] = data['business']
            del data['business']
        
        # Flatten customer to reviewer
        if 'customer' in data:
            data['reviewer'] = data['customer']
            del data['customer']
        
        # Rename comment to description
        if 'comment' in data:
            data['description'] = data['comment']
            del data['comment']
        
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """
    Base Serializer for Review.
    
    Uses ModelSerializer which automatically includes all model fields.
    The model fields (customer, business, order, rating, comment) come from the model.
    """
    
    class Meta:
        model = Review
        fields = ['id', 'customer', 'business', 'order', 'rating', 'comment', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_rating(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Rating must be an integer, not a string.")
        return value


class ReviewCreateSerializer(serializers.Serializer):
    """Serializer for creating a Review"""
    business_user = serializers.IntegerField(required=True, write_only=True)
    rating = serializers.IntegerField(required=True)
    description = serializers.CharField(required=True, allow_blank=True)
    
    def validate_business_user(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Business user ID must be an integer, not a string.")
        from accounts_app.models import User
        try:
            user = User.objects.get(pk=value)
            if user.user_type != 'business':
                raise serializers.ValidationError("The specified user is not a business user.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("The specified business user was not found.")
    
    def validate_rating(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Rating must be an integer, not a string.")
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
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def validate_rating(self, value):
        if isinstance(value, str):
            raise serializers.ValidationError("Rating must be an integer, not a string.")
        return value
    
    def update(self, instance, validated_data):
        """Update only rating and comment"""
        if 'comment' in validated_data:
            instance.comment = validated_data['comment']
        if 'rating' in validated_data:
            instance.rating = validated_data['rating']
        instance.save()
        return instance
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Converts the response structure to match frontend expectations:
        - Renames 'comment' to 'description'
        """
        data = super().to_representation(instance)
        if 'comment' in data:
            data['description'] = data['comment']
            del data['comment']
        return data