from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from accounts_app.models import BusinessProfile, CustomerProfile, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type']
        read_only_fields = ['id']


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Creates a new User and corresponding BusinessProfile or CustomerProfile.
    
    Validates password match, creates user with hashed password, and automatically
    creates the appropriate profile (BusinessProfile for 'business' type, CustomerProfile
    for 'customer' type) with default empty values.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True, required=True)
    type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'first_name', 'last_name', 'type']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def _create_user_profile(self, user, user_type):
        if user_type == 'business':
            BusinessProfile.objects.create(user=user)
        elif user_type == 'customer':
            CustomerProfile.objects.create(user=user)
    
    def create(self, validated_data):
        validated_data.pop('repeated_password')
        user_type = validated_data.pop('type')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(user_type=user_type, **validated_data)
        user.set_password(password)
        user.save()
        
        self._create_user_profile(user, user_type)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for User Login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class BusinessProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Business Profile.
    
    Uses ModelSerializer which automatically includes all model fields.
    The nested 'user' field provides full user information via UserSerializer.
    Uses to_representation() to add 'username' for a flatter API response structure.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BusinessProfile
        fields = ['id', 'user', 'company_name', 'description', 'phone', 
                 'email', 'location', 'working_hours', 'profile_picture', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Adds 'username' field from user.username for convenience.
        """
        data = super().to_representation(instance)
        if 'user' in data and isinstance(data['user'], dict) and 'username' in data['user']:
            data['username'] = data['user']['username']
        return data
    
    def validate_company_name(self, value):
        """Validate company name - ensure it's not empty."""
        if not value:
            raise serializers.ValidationError("Company name cannot be empty.")
        return value


class CustomerProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for Customer Profile.
    
    Uses ModelSerializer which automatically includes all model fields.
    The nested 'user' field provides full user information via UserSerializer.
    Uses to_representation() to add 'username' for a flatter API response structure.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CustomerProfile
        fields = ['id', 'user', 'bio', 'phone', 'email', 
                 'location', 'profile_picture', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """
        Format the output representation.
        
        Adds 'username' field from user.username for convenience.
        """
        data = super().to_representation(instance)
        if 'user' in data and isinstance(data['user'], dict) and 'username' in data['user']:
            data['username'] = data['user']['username']
        return data


class ProfileDetailSerializer(serializers.Serializer):
    """
    Flattens User and Profile data into a single response structure.
    
    Profile is created during registration, so it always exists. Model fields
    have default='' values, so no additional null checks are needed.
    """
    
    def get_file(self, user):
        if user.user_type == 'business':
            profile = user.business_profile
        elif user.user_type == 'customer':
            profile = user.customer_profile
        else:
            return ''
        
        if profile.profile_picture:
            file_name = str(profile.profile_picture)
            return file_name.split('/')[-1] if '/' in file_name else file_name
        return ''
    
    def to_representation(self, instance):
        if not isinstance(instance, User):
            return super().to_representation(instance)
        
        if instance.user_type == 'business':
            profile = instance.business_profile
            description = profile.description
            working_hours = profile.working_hours
        elif instance.user_type == 'customer':
            profile = instance.customer_profile
            description = profile.bio
            working_hours = ''
        else:
            profile = None
            description = ''
            working_hours = ''
        
        return {
            'user': instance.id,
            'username': instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'type': instance.user_type,
            'email': profile.email if profile.email else instance.email,
            'created_at': profile.created_at if profile else None,
            'file': self.get_file(instance),
            'location': profile.location if profile else '',
            'tel': profile.phone if profile else '',
            'description': description,
            'working_hours': working_hours
        }

