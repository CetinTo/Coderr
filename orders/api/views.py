from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsBusinessPartner, IsCustomerUser, IsOrderParticipant, IsStaff
from ..models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderListSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


class NoPagination(PageNumberPagination):
    """Disables pagination for Orders"""
    page_size = None


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for Orders"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    pagination_class = NoPagination
    
    def get_permissions(self):
        """Permissions depending on action"""
        if self.action == 'list':
            # Authenticated users can list (filtered by get_queryset)
            permission_classes = [IsAuthenticated]
        elif self.action == 'retrieve':
            # Only order participants can view specific order
            permission_classes = [IsAuthenticated, IsOrderParticipant]
        elif self.action == 'create':
            # Only customer users can create orders
            permission_classes = [IsAuthenticated, IsCustomerUser]
        elif self.action in ['update', 'partial_update']:
            # Only business partner can update order status
            permission_classes = [IsAuthenticated, IsBusinessPartner]
        elif self.action == 'destroy':
            # Orders cannot be deleted - permission check will always fail
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Only own orders or orders for own offers"""
        user = self.request.user
        # Returns orders where the user is either customer or business partner
        # Handle both cases: offer exists and offer is deleted (NULL)
        return Order.objects.filter(
            Q(customer=user) | Q(offer__creator=user) | Q(customer=user, offer__isnull=True)
        ).distinct()
    
    def get_serializer_class(self):
        """Use different serializers depending on action"""
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return OrderUpdateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new order with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Return response with OrderListSerializer
        response_serializer = OrderListSerializer(order)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Update an order with validation"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return response with OrderListSerializer
        response_serializer = OrderListSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        """Orders cannot be deleted once created."""
        return Response(
            {'error': 'Orders cannot be deleted once they have been created.'},
            status=status.HTTP_403_FORBIDDEN
        )


class OrderCountView(APIView):
    """API view for count of in-progress orders for a business user."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from accounts_app.models import User
        business_user_id = self.kwargs.get('business_user_id')
        try:
            user = User.objects.get(id=business_user_id)
            if user.user_type != 'business':
                return Order.objects.none()
            return Order.objects.filter(
                offer__creator=user,
                status='in_progress'
            )
        except User.DoesNotExist:
            return Order.objects.none()
    
    def get(self, request, business_user_id):
        from accounts_app.models import User
        try:
            user = User.objects.get(id=business_user_id)
            
            if user.user_type != 'business':
                return Response(
                    {'error': 'No business user found with the specified ID'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            count = Order.objects.filter(
                offer__creator=user,
                status='in_progress'
            ).count()
            
            return Response({'order_count': count}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'No business user found with the specified ID'},
                status=status.HTTP_404_NOT_FOUND
            )


class CompletedOrderCountView(APIView):
    """API view for count of completed orders for a business user."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from accounts_app.models import User
        business_user_id = self.kwargs.get('business_user_id')
        try:
            user = User.objects.get(id=business_user_id)
            if user.user_type != 'business':
                return Order.objects.none()
            return Order.objects.filter(
                offer__creator=user,
                status='completed'
            )
        except User.DoesNotExist:
            return Order.objects.none()
    
    def get(self, request, business_user_id):
        from accounts_app.models import User
        try:
            user = User.objects.get(id=business_user_id)
            
            if user.user_type != 'business':
                return Response(
                    {'error': 'No business user found with the specified ID'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            count = Order.objects.filter(
                offer__creator=user,
                status='completed'
            ).count()
            
            return Response({'completed_order_count': count}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'No business user found with the specified ID'},
                status=status.HTTP_404_NOT_FOUND
            )
