# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# 3. Lokale Importe
from .api.permissions import IsBusinessUser, IsOfferOwner
from .models import Offer, OfferDetail
from .pagination import OfferPagination
from .serializers import (
    OfferCreateResponseSerializer,
    OfferCreateSerializer,
    OfferDetailResponseSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
    OfferSerializer,
    OfferUpdateSerializer,
)


class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for Offers with filtering"""
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    pagination_class = OfferPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['creator']
    search_fields = ['title', 'description']
    # ordering_fields are handled manually in get_queryset() since min_price is an annotation
    ordering = ['-updated_at']
    
    def get_serializer_class(self):
        """Use different serializers depending on action"""
        if self.action == 'list':
            return OfferListSerializer
        elif self.action == 'create':
            return OfferCreateSerializer
        elif self.action == 'retrieve':
            return OfferDetailResponseSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return OfferUpdateSerializer
        return OfferSerializer
    
    def get_serializer_context(self):
        """Add request to serializer context"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_permissions(self):
        """Permissions depending on action"""
        if self.action == 'list':
            permission_classes = [AllowAny]
        elif self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated, IsBusinessUser]
        else:
            permission_classes = [IsAuthenticated, IsOfferOwner]
        return [permission() for permission in permission_classes]
    
    def _validate_query_params(self):
        """Validate query parameters and raise ValidationError if invalid."""
        max_delivery_time = self.request.query_params.get('max_delivery_time', None)
        if max_delivery_time and max_delivery_time.strip():
            # Remove quotes if present
            max_delivery_time = max_delivery_time.strip().strip('"').strip("'")
            try:
                int(max_delivery_time)
            except (ValueError, TypeError):
                raise ValidationError({
                    'max_delivery_time': 'max_delivery_time must be a valid integer.'
                })
        
        min_price = self.request.query_params.get('min_price', None)
        if min_price and min_price.strip():
            # Remove quotes if present
            min_price = min_price.strip().strip('"').strip("'")
            try:
                float(min_price)
            except (ValueError, TypeError):
                raise ValidationError({
                    'min_price': 'min_price must be a valid number.'
                })
        
        creator_id = self.request.query_params.get('creator_id', None)
        if creator_id and creator_id.strip():
            # Remove quotes if present
            creator_id = creator_id.strip().strip('"').strip("'")
            try:
                int(creator_id)
            except (ValueError, TypeError):
                raise ValidationError({
                    'creator_id': 'creator_id must be a valid integer.'
                })
    
    def _apply_filters(self, queryset):
        """Apply filters to queryset."""
        creator_id = self.request.query_params.get('creator_id', None)
        if creator_id and creator_id.strip():
            creator_id = creator_id.strip().strip('"').strip("'")
            queryset = queryset.filter(creator_id=int(creator_id))
        
        max_delivery_time = self.request.query_params.get('max_delivery_time', None)
        if max_delivery_time and max_delivery_time.strip():
            max_delivery_time = max_delivery_time.strip().strip('"').strip("'")
            max_days = int(max_delivery_time)
            queryset = queryset.filter(
                details__delivery_time_in_days__lte=max_days
            ).distinct()
        
        min_price = self.request.query_params.get('min_price', None)
        if min_price and min_price.strip():
            min_price = min_price.strip().strip('"').strip("'")
            min_price_float = float(min_price)
            queryset = queryset.filter(
                details__price__gte=min_price_float
            ).distinct()
        
        return queryset
    
    def _apply_ordering(self, queryset, ordering, needs_annotation):
        """Apply ordering to queryset."""
        if not ordering or not ordering.strip():
            return queryset.order_by('-updated_at')
        
        ordering = ordering.strip()
        if ordering == 'updated_at':
            return queryset.order_by('updated_at')
        if ordering == '-updated_at':
            return queryset.order_by('-updated_at')
        if ordering == 'min_price':
            if needs_annotation:
                return queryset.order_by('min_price_value', '-updated_at')
            return queryset.annotate(
                min_price_value=Min('details__price')
            ).order_by('min_price_value', '-updated_at')
        if ordering == '-min_price':
            if needs_annotation:
                return queryset.order_by('-min_price_value', '-updated_at')
            return queryset.annotate(
                min_price_value=Min('details__price')
            ).order_by('-min_price_value', '-updated_at')
        
        return queryset.order_by('-updated_at')
    
    def get_queryset(self):
        """Custom QuerySet with filtering and sorting."""
        queryset = Offer.objects.all()
        ordering = self.request.query_params.get('ordering', None)
        needs_annotation = ordering and ordering.strip() in ['min_price', '-min_price']
        
        if needs_annotation:
            queryset = queryset.annotate(min_price_value=Min('details__price'))
        
        queryset = self._apply_filters(queryset)
        queryset = self._apply_ordering(queryset, ordering, needs_annotation)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List offers with query parameter validation."""
        # Validate query parameters - this will raise ValidationError if invalid
        try:
            self._validate_query_params()
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Create a new offer with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return response with OfferCreateResponseSerializer
        response_serializer = OfferCreateResponseSerializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Set creator when creating"""
        serializer.save(creator=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Update an offer with ownership check"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return response with OfferCreateResponseSerializer (same structure as CREATE)
        response_serializer = OfferCreateResponseSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    
    def perform_update(self, serializer):
        """Perform the update"""
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Delete an offer with ownership check"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OfferDetailView(APIView):
    """API view for single OfferDetail."""
    permission_classes = [IsAuthenticated]
    serializer_class = OfferDetailSerializer
    
    def get_queryset(self):
        """Get all offer details."""
        return OfferDetail.objects.all()
    
    def get(self, request, pk):
        """Get single OfferDetail."""
        try:
            offer_detail = self.get_queryset().get(pk=pk)
            serializer = OfferDetailSerializer(offer_detail)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except OfferDetail.DoesNotExist:
            return Response(
                {'error': 'OfferDetail not found'},
                status=status.HTTP_404_NOT_FOUND
            )
