# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import filters, status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# 3. Lokale Importe
from .api.permissions import IsCustomerUser, IsReviewOwner
from .models import Review
from .serializers import (
    ReviewCreateSerializer,
    ReviewListSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)


class ReviewPagination(PageNumberPagination):
    """Pagination for Reviews - all results by default, but page_size=6 when requested"""
    page_size = None  # No pagination by default
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, view=None):
        """Paginate only when page_size is explicitly specified"""
        page_size = request.query_params.get(self.page_size_query_param)
        if page_size is not None:
            try:
                self.page_size = int(page_size)
            except (TypeError, ValueError):
                pass
        return super().paginate_queryset(queryset, request, view)


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for Reviews"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    pagination_class = ReviewPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['updated_at', 'rating']
    ordering = ['-updated_at']
    
    def get_permissions(self):
        """Permissions depending on action"""
        if self.action in ['list', 'retrieve']:
            # Authenticated users can view reviews
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            # Only customer users can create reviews
            permission_classes = [IsAuthenticated, IsCustomerUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only review owners can update/delete
            permission_classes = [IsAuthenticated, IsReviewOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter reviews by business or reviewer"""
        queryset = Review.objects.all()
        business_user_id = self.request.query_params.get('business_user_id', None)
        reviewer_id = self.request.query_params.get('reviewer_id', None)
        
        if business_user_id:
            try:
                queryset = queryset.filter(business_id=int(business_user_id))
            except ValueError:
                pass
        
        if reviewer_id:
            try:
                queryset = queryset.filter(customer_id=int(reviewer_id))
            except ValueError:
                pass
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers depending on action"""
        if self.action == 'list':
            return ReviewListSerializer
        elif self.action == 'create':
            return ReviewCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new review with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Return response with ReviewListSerializer
        response_serializer = ReviewListSerializer(review)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Update a review with ownership check"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return response with ReviewListSerializer
        response_serializer = ReviewListSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    def perform_update(self, serializer):
        """Perform the update"""
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Delete a review with ownership check"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
