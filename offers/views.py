# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
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
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def _apply_filters(self, queryset):
        """Apply filters to queryset."""
        creator_id = self.request.query_params.get('creator_id', None)
        if creator_id and creator_id.strip():
            try:
                queryset = queryset.filter(creator_id=int(creator_id))
            except (ValueError, TypeError):
                pass
        
        max_delivery_time = self.request.query_params.get('max_delivery_time', None)
        if max_delivery_time and max_delivery_time.strip():
            try:
                max_days = int(max_delivery_time)
                queryset = queryset.filter(
                    details__delivery_time_in_days__lte=max_days
                ).distinct()
            except (ValueError, TypeError):
                pass
        
        min_price = self.request.query_params.get('min_price', None)
        if min_price and min_price.strip():
            try:
                min_price_float = float(min_price)
                queryset = queryset.filter(
                    details__price__gte=min_price_float
                ).distinct()
            except (ValueError, TypeError):
                pass
        
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
