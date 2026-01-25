from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .filters import OfferFilterBackend, OfferOrderingFilter
from .permissions import IsBusinessUser, IsOfferOwner
from ..models import Offer, OfferDetail
from ..pagination import OfferPagination
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
    """
    ViewSet for Offers with custom filtering, ordering, and search.
    
    Uses prefetch_related('details') and select_related('creator') to prevent N+1 queries.
    Without prefetch_related, 200 offers would trigger 201 queries (1 + 200 for details).
    With prefetch_related, it's only 2 queries total.
    """
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    pagination_class = OfferPagination
    filter_backends = [OfferFilterBackend, OfferOrderingFilter, filters.SearchFilter]
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        """
        Optimized queryset with prefetch_related, select_related, and annotations.
        
        Prevents N+1 queries: Without prefetch_related, accessing obj.details.all() for 200 offers
        would trigger 200 additional queries. With prefetch_related, it's only 2 queries total.
        """
        from django.db.models import Min
        return (
            Offer.objects
            .select_related('creator')
            .prefetch_related('details')
            .annotate(min_price=Min('details__price'))
            .annotate(min_delivery_time=Min('details__delivery_time_in_days'))
            .all()
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OfferListSerializer
        elif self.action == 'create':
            return OfferCreateSerializer
        elif self.action == 'retrieve':
            return OfferDetailResponseSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return OfferUpdateSerializer
        return OfferSerializer
    
    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        elif self.action == 'retrieve':
            permission_classes = [IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [IsAuthenticated, IsBusinessUser]
        else:
            permission_classes = [IsAuthenticated, IsOfferOwner]
        return [permission() for permission in permission_classes]
    
    def create(self, request, *args, **kwargs):
        """Uses OfferCreateResponseSerializer for response instead of OfferCreateSerializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_serializer = OfferCreateResponseSerializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Uses OfferCreateResponseSerializer for response instead of OfferUpdateSerializer."""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        instance.refresh_from_db()
        response_serializer = OfferCreateResponseSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class OfferDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OfferDetailSerializer
    
    def get_queryset(self):
        return OfferDetail.objects.select_related('offer', 'offer__creator').all()
    
    def get(self, request, pk):
        try:
            offer_detail = self.get_queryset().get(pk=pk)
            serializer = OfferDetailSerializer(offer_detail)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except OfferDetail.DoesNotExist:
            return Response(
                {'error': 'OfferDetail not found'},
                status=status.HTTP_404_NOT_FOUND
            )
