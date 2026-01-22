from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from accounts_app.models import BusinessProfile, CustomerProfile, User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type']
        read_only_fields = ['id']
    
    def validate_username(self, value):
        """Validate username."""
        if not value:
            raise serializers.ValidationError("Username cannot be empty.")
        return value
    
    def validate_email(self, value):
        """Validate email."""
        if not value:
            raise serializers.ValidationError("Email cannot be empty.")
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for User Registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True, required=True)
    type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'first_name', 'last_name', 'type']
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def _create_user_profile(self, user, user_type):
        """Create corresponding profile based on user type."""
        if user_type == 'business':
            BusinessProfile.objects.create(user=user)
        elif user_type == 'customer':
            CustomerProfile.objects.create(user=user)
    
    def create(self, validated_data):
        """Create a new user with profile."""
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
    """Serializer for Profile Detail Response (flat structure)"""
    user = serializers.IntegerField(source='id')
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    file = serializers.SerializerMethodField()
    location = serializers.CharField()
    tel = serializers.CharField(source='phone')
    description = serializers.CharField()
    working_hours = serializers.CharField(required=False, allow_blank=True)
    type = serializers.CharField(source='user_type')
    email = serializers.CharField()
    created_at = serializers.DateTimeField()
    
    def get_file(self, user):
        """Returns the filename of the profile picture"""
        try:
            if user.user_type == 'business':
                profile = user.business_profile
            elif user.user_type == 'customer':
                profile = user.customer_profile
            else:
                return ''
            
            if profile and profile.profile_picture:
                file_name = str(profile.profile_picture)
                return file_name.split('/')[-1] if '/' in file_name else file_name
        except:
            pass
        return ''
    
    def _get_profile_data(self, user):
        """Extract profile data based on user type."""
        from accounts_app.models import BusinessProfile, CustomerProfile
        
        if user.user_type == 'business':
            try:
                profile = user.business_profile
                return {
                    'profile': profile,
                    'description': profile.description or '',
                    'working_hours': profile.working_hours or '',
                    'email': profile.email or user.email or '',
                    'created_at': profile.created_at
                }
            except BusinessProfile.DoesNotExist:
                return {
                    'profile': None,
                    'description': '',
                    'working_hours': '',
                    'email': user.email or '',
                    'created_at': None
                }
        elif user.user_type == 'customer':
            try:
                profile = user.customer_profile
                return {
                    'profile': profile,
                    'description': profile.bio or '',
                    'working_hours': '',
                    'email': profile.email or user.email or '',
                    'created_at': profile.created_at
                }
            except CustomerProfile.DoesNotExist:
                return {
                    'profile': None,
                    'description': '',
                    'working_hours': '',
                    'email': user.email or '',
                    'created_at': None
                }
        return {
            'profile': None,
            'description': '',
            'working_hours': '',
            'email': user.email or '',
            'created_at': None
        }
    
    def _build_profile_dict(self, user, profile_data):
        """Build profile dictionary for response."""
        profile = profile_data['profile']
        base_dict = {
            'user': user.id,
            'username': user.username or '',
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'type': user.user_type,
            'email': profile_data['email'],
            'created_at': profile_data['created_at']
        }
        
        if profile:
            base_dict.update({
                'file': self.get_file(user),
                'location': profile.location or '',
                'tel': profile.phone or '',
                'description': profile_data['description'],
                'working_hours': profile_data['working_hours']
            })
        else:
            base_dict.update({
                'file': '',
                'location': '',
                'tel': '',
                'description': profile_data['description'],
                'working_hours': profile_data['working_hours']
            })
        return base_dict
    
    def to_representation(self, instance):
        """Creates the flat response structure."""
        from accounts_app.models import BusinessProfile, CustomerProfile
        
        if not isinstance(instance, User):
            return super().to_representation(instance)
        
        try:
            profile_data = self._get_profile_data(instance)
            return self._build_profile_dict(instance, profile_data)
        except (BusinessProfile.DoesNotExist, CustomerProfile.DoesNotExist):
            return self._build_profile_dict(
                instance,
                {
                    'profile': None,
                    'description': '',
                    'working_hours': '',
                    'email': instance.email or '',
                    'created_at': None
                }
            )

