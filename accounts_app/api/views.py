# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# 3. Lokale Importe
from accounts_app.api.serializers import (
    BusinessProfileSerializer,
    CustomerProfileSerializer,
    LoginSerializer,
    ProfileDetailSerializer,
    RegistrationSerializer,
    UserSerializer,
)
from accounts_app.models import BusinessProfile, CustomerProfile, User


class RegistrationView(APIView):
    """API view for user registration."""
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer
    
    def post(self, request):
        """Register a new user."""
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """API view for user login."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        """User login."""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def _get_profile_data(user):
    """Get profile data based on user type."""
    if user.user_type == 'business':
        try:
            profile = user.business_profile
            return BusinessProfileSerializer(profile).data
        except BusinessProfile.DoesNotExist:
            return None
    elif user.user_type == 'customer':
        try:
            profile = user.customer_profile
            return CustomerProfileSerializer(profile).data
        except CustomerProfile.DoesNotExist:
            return None
    return None


class ProfileView(APIView):
    """API view for current authenticated user's profile."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get(self, request):
        """Get current authenticated user's profile."""
        user = request.user
        serializer = UserSerializer(user)
        data = serializer.data
        data['profile'] = _get_profile_data(user)
        return Response(data)


class BusinessProfilesView(APIView):
    """API view for listing all business profiles."""
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileDetailSerializer
    
    def get_queryset(self):
        """Get all business users."""
        return User.objects.filter(user_type='business')
    
    def get(self, request):
        """List all business profiles."""
        business_users = self.get_queryset()
        serializer = ProfileDetailSerializer()
        
        result = []
        for user in business_users:
            result.append(serializer.to_representation(user))
        
        return Response(result, status=status.HTTP_200_OK)


class CustomerProfilesView(APIView):
    """API view for listing all customer profiles."""
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileDetailSerializer
    
    def get_queryset(self):
        """Get all customer users."""
        return User.objects.filter(user_type='customer')
    
    def get(self, request):
        """List all customer profiles."""
        customer_users = self.get_queryset()
        serializer = ProfileDetailSerializer()
        
        result = []
        for user in customer_users:
            result.append(serializer.to_representation(user))
        
        return Response(result, status=status.HTTP_200_OK)


def _update_user_fields(user, data):
    """Update user first_name and last_name fields."""
    if 'first_name' in data:
        user.first_name = data.get('first_name', '') or ''
    if 'last_name' in data:
        user.last_name = data.get('last_name', '') or ''
    user.save()


def _update_business_profile(user, data):
    """Update business profile fields."""
    profile = get_object_or_404(BusinessProfile, user=user)
    if 'description' in data:
        profile.description = data.get('description', '') or ''
    if 'tel' in data or 'phone' in data:
        profile.phone = data.get('tel') or data.get('phone', '') or ''
    if 'email' in data:
        profile.email = data.get('email', '') or ''
        user.email = profile.email
    if 'location' in data:
        profile.location = data.get('location', '') or ''
    if 'working_hours' in data:
        profile.working_hours = data.get('working_hours', '') or ''
    profile.save()
    user.save()


def _update_customer_profile(user, data):
    """Update customer profile fields."""
    profile = get_object_or_404(CustomerProfile, user=user)
    if 'description' in data:
        profile.bio = data.get('description', '') or ''
    if 'tel' in data or 'phone' in data:
        profile.phone = data.get('tel') or data.get('phone', '') or ''
    if 'email' in data:
        profile.email = data.get('email', '') or ''
        user.email = profile.email
    if 'location' in data:
        profile.location = data.get('location', '') or ''
    profile.save()
    user.save()


def _get_profile_response(user):
    """Get profile detail response."""
    serializer = ProfileDetailSerializer(user)
    return Response(serializer.to_representation(user))


class ProfileDetailView(APIView):
    """API view for getting or updating profile detail."""
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileDetailSerializer
    
    def get_queryset(self):
        """Get all users."""
        return User.objects.all()
    
    def get(self, request, pk):
        """Get profile detail."""
        try:
            user = self.get_queryset().get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        return _get_profile_response(user)
    
    def patch(self, request, pk):
        """Update profile detail."""
        try:
            user = self.get_queryset().get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.user.id != user.id:
            return Response(
                {'error': 'You can only edit your own profile'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        _update_user_fields(user, request.data)
        
        if user.user_type == 'business':
            _update_business_profile(user, request.data)
        elif user.user_type == 'customer':
            _update_customer_profile(user, request.data)
        else:
            return Response(
                {'error': 'Invalid user type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return _get_profile_response(user)


class BaseInfoView(APIView):
    """API view for base information for the homepage."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get base information."""
        from django.db.models import Avg
        from offers.models import Offer
        from reviews.models import Review
        
        review_count = Review.objects.count()
        
        avg_rating_result = Review.objects.aggregate(Avg('rating'))
        average_rating = round(avg_rating_result['rating__avg'] or 0, 1)
        
        business_profile_count = BusinessProfile.objects.count()
        
        offer_count = Offer.objects.count()
        
        return Response({
            'review_count': review_count,
            'average_rating': average_rating,
            'business_profile_count': business_profile_count,
            'offer_count': offer_count,
        }, status=status.HTTP_200_OK)
