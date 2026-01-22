"""Custom filters for offers app API."""
from django.db.models import Min
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend


class OfferFilterBackend(DjangoFilterBackend):
    """
    Custom filter backend for offers with query parameter validation.
    
    This filter backend handles custom query parameters for filtering offers:
    - creator_id: Filter offers by creator user ID
    - min_price: Filter offers with minimum price (searches in related OfferDetail prices)
    - max_delivery_time: Filter offers with maximum delivery time (searches in related OfferDetail)
    
    The backend validates all query parameters before applying filters to ensure
    type safety and prevent invalid queries.
    
    Performance Note:
        The queryset passed to this backend should already have prefetch_related('details')
        from get_queryset() in the ViewSet. However, when filtering by details__price
        or details__delivery_time_in_days, Django uses JOIN operations which are efficient.
        The prefetch_related is still important for serialization after filtering.
    """
    
    def filter_queryset(self, request, queryset, view):
        params = request.query_params
        
        creator_id = params.get('creator_id', '').strip().strip('"').strip("'")
        if creator_id:
            try:
                queryset = queryset.filter(creator_id=int(creator_id))
            except (ValueError, TypeError):
                raise ValidationError({'creator_id': 'creator_id must be a valid integer.'})
        
        max_delivery_time = params.get('max_delivery_time', '').strip().strip('"').strip("'")
        if max_delivery_time:
            try:
                queryset = queryset.filter(details__delivery_time_in_days__lte=int(max_delivery_time)).distinct()
            except (ValueError, TypeError):
                raise ValidationError({'max_delivery_time': 'max_delivery_time must be a valid integer.'})
        
        min_price = params.get('min_price', '').strip().strip('"').strip("'")
        if min_price:
            try:
                queryset = queryset.filter(details__price__gte=float(min_price)).distinct()
            except (ValueError, TypeError):
                raise ValidationError({'min_price': 'min_price must be a valid number.'})
        
        return queryset


class OfferOrderingFilter(BaseFilterBackend):
    """Custom ordering filter for offers with min_price support."""
    
    def filter_queryset(self, request, queryset, view):
        ordering = request.query_params.get('ordering', '').strip()
        
        if not ordering:
            return queryset.order_by('-updated_at')
        
        if ordering in ['min_price', '-min_price']:
            queryset = queryset.annotate(min_price_value=Min('details__price'))
            return queryset.order_by('min_price_value' if ordering == 'min_price' else '-min_price_value', '-updated_at')
        
        if ordering in ['updated_at', '-updated_at']:
            return queryset.order_by(ordering)
        
        return queryset.order_by('-updated_at')
