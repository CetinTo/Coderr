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
    ViewSet for Offers with filtering, ordering, and search capabilities.
    
    Provides CRUD operations for Offer model with:
    - Custom filtering via OfferFilterBackend (creator_id, min_price, max_delivery_time)
    - Custom ordering via OfferOrderingFilter (updated_at, min_price)
    - Search functionality via SearchFilter (title, description)
    - Dynamic permissions based on action (AllowAny for list, IsAuthenticated for retrieve, etc.)
    - Different serializers for different actions (create, update, list, retrieve)
    - Optimized database queries using prefetch_related and select_related
    
    The ViewSet automatically handles:
    - Setting creator field from authenticated user on create
    - Using OfferCreateResponseSerializer for create/update responses
    - Permission checks based on action and ownership
    - Database query optimization to prevent N+1 query problems
    
    Performance Optimization:
    - Uses prefetch_related('details') to load all related OfferDetail objects in a single query
      instead of querying the database for each offer's details separately. This prevents
      N+1 query problems when serializing offers with their details.
    - Uses select_related('creator') to load the creator user in the same query as the offer,
      avoiding additional queries when accessing creator information.
    - These optimizations are critical for performance when dealing with large datasets
      (e.g., 200 offers with 3 details each = 600 detail records). Without prefetch_related,
      this would result in 201 database queries (1 for offers + 200 for details). With
      prefetch_related, it's only 2 queries (1 for offers + 1 for all details).
    """
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    pagination_class = OfferPagination
    filter_backends = [OfferFilterBackend, OfferOrderingFilter, filters.SearchFilter]
    search_fields = ['title', 'description']
    
    def get_queryset(self):
        """
        Return an optimized queryset with prefetch_related, select_related, and annotations.
        
        This method is crucial for database performance. It uses Django's prefetch_related,
        select_related, and annotate to optimize database queries and prevent N+1 query problems.
        
        Performance Impact:
        - Without prefetch_related: For 200 offers, accessing obj.details.all() in serializers
          would trigger 200 additional database queries (one per offer), resulting in 201 total
          queries (1 for offers + 200 for details).
        - With prefetch_related: All related details are loaded in a single additional query,
          resulting in only 2 total queries (1 for offers + 1 for all details).
        - With annotate: Calculated fields (min_price, min_delivery_time) are computed in the
          database query itself, avoiding Python-level calculations and additional queries.
        
        The queryset includes:
        - select_related('creator'): Joins the creator User in the same query as the Offer,
          avoiding additional queries when accessing creator information.
        - prefetch_related('details'): Pre-loads all OfferDetail objects related to each Offer
          in a single query. This is essential because serializers access obj.details.all()
          for each offer, which would otherwise trigger separate queries.
        - annotate(min_price=Min('details__price')): Calculates minimum price of all details
          directly in the database query, making it available as obj.min_price without
          additional queries or Python calculations.
        - annotate(min_delivery_time=Min('details__delivery_time_in_days')): Calculates minimum
          delivery time of all details directly in the database query, making it available as
          obj.min_delivery_time without additional queries or Python calculations.
        
        Returns:
            QuerySet: Optimized queryset with prefetched details, selected creator, and
                     annotated calculated fields (min_price, min_delivery_time)
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
        """
        Return the appropriate serializer class based on the current action.
        
        The serializer class determines both the input validation and response format.
        Different serializers are used for different operations to optimize the
        data structure and validation rules.
        
        Returns:
            - OfferListSerializer: For list action (GET /api/offers/)
              Provides minimal data for listing multiple offers
            - OfferCreateSerializer: For create action (POST /api/offers/)
              Validates input data including nested details array
            - OfferDetailResponseSerializer: For retrieve action (GET /api/offers/{id}/)
              Provides full offer details with calculated fields (min_price, min_delivery_time)
            - OfferUpdateSerializer: For update/partial_update actions (PATCH/PUT /api/offers/{id}/)
              Allows partial updates with nested details validation
            - OfferSerializer: Default serializer for other actions
        """
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
        """
        Return the appropriate permission classes based on the current action.
        
        Permissions are dynamically assigned based on the HTTP method and action:
        - List operations are public (AllowAny) to enable browsing offers
        - Retrieve operations require authentication (IsAuthenticated)
        - Create operations require authentication AND business user status (IsBusinessUser)
        - Update/Delete operations require authentication AND ownership (IsOfferOwner)
        
        Returns:
            List of permission instances appropriate for the current action
        """
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
        """
        Create a new offer and return it with OfferCreateResponseSerializer.
        
        This method is overridden to use a different response serializer (OfferCreateResponseSerializer)
        than the input serializer (OfferCreateSerializer). The creator is automatically set
        via perform_create() using the authenticated user from the request.
        
        The standard create() flow is followed:
        1. Get serializer with request data (OfferCreateSerializer)
        2. Validate data (raises exception if invalid)
           - Validates title, description, image
           - Validates details array (must contain exactly 3 details: basic, standard, premium)
           - Validates each detail's fields (price, delivery_time_in_days, revisions, etc.)
        3. Call perform_create() to save with creator
           - Creates the Offer instance
           - Creates 3 OfferDetail instances (one for each tier)
        4. Return response with OfferCreateResponseSerializer
           - Uses different serializer for response to match frontend expectations
           - Includes all offer fields plus nested details array
        
        After creation, the offer instance is automatically prefetched with details
        to avoid additional queries when serializing the response.
        
        Args:
            request: HTTP request object containing offer data:
                - title (string, required): Title of the offer
                - description (string, required): Description of the offer
                - image (file, optional): Image file for the offer
                - details (array, required): Array of exactly 3 detail objects:
                    - Each detail must have offer_type ('basic', 'standard', or 'premium')
                    - Each detail must have price (number), delivery_time_in_days (integer),
                      revisions (integer), title (string), features (array of strings)
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        
        Returns:
            Response: HTTP 201 Created response with serialized offer data using OfferCreateResponseSerializer.
                     The response includes the created offer with all its details.
        
        Raises:
            ValidationError: If the input data is invalid (e.g., wrong number of details,
                           invalid offer_type, missing required fields, etc.)
            PermissionDenied: If the user is not authenticated or not a business user
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_serializer = OfferCreateResponseSerializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """
        Set the creator field to the authenticated user when creating a new offer.
        
        This method is called by create() after validation. The creator field is not
        included in the request data (for security reasons) and must be set from the
        authenticated user. The creator is automatically assigned from request.user.
        
        The serializer.save() method:
        1. Creates the Offer instance with the provided data
        2. Sets the creator field to request.user
        3. Creates the related OfferDetail instances (3 details: basic, standard, premium)
        
        After saving, the serializer.instance contains the created Offer with all
        related OfferDetail objects already loaded, so no additional queries are needed
        when serializing the response.
        
        Args:
            serializer: Validated OfferCreateSerializer instance ready to be saved.
                       The serializer has already validated:
                       - Title and description are not empty
                       - Details array contains exactly 3 items
                       - Each detail has valid offer_type, price, delivery_time_in_days, etc.
        
        Note:
            The creator is set from request.user, which is guaranteed to be authenticated
            and a business user due to the permission checks in get_permissions().
        """
        serializer.save(creator=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """
        Update an existing offer and return it with OfferCreateResponseSerializer.
        
        This method is overridden to use OfferCreateResponseSerializer for the response,
        ensuring consistent response format between create and update operations.
        The update is always partial (PATCH semantics) - only provided fields are updated.
        
        The standard update() flow is followed:
        1. Get the offer instance by ID (from get_object())
           - Uses the optimized queryset from get_queryset() which includes prefetch_related('details')
           - Ensures details are already loaded to avoid additional queries
        2. Get serializer with instance and request data (partial=True is default in DRF)
           - Uses OfferUpdateSerializer for input validation
           - Allows partial updates (only provided fields are validated and updated)
        3. Validate data (raises exception if invalid)
           - Validates provided fields (title, description, image, details)
           - If details are provided, validates the entire details array structure
        4. Call perform_update() to save changes
           - Updates Offer fields if provided
           - Updates or creates OfferDetail instances if details are provided
        5. Refresh the instance to ensure we have the latest data
        6. Return response with OfferCreateResponseSerializer
        
        Performance Note:
            The instance retrieved via get_object() already has details prefetched from
            get_queryset(), so accessing instance.details in the response serializer
            does not trigger additional database queries.
        
        Args:
            request: HTTP request object containing update data (partial fields allowed):
                - title (string, optional): New title for the offer
                - description (string, optional): New description for the offer
                - image (file, optional): New image file for the offer
                - details (array, optional): Array of detail objects to update:
                    - Each detail must have offer_type to identify which detail to update
                    - Only provided fields in each detail are updated
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments (includes 'pk' for the offer ID)
        
        Returns:
            Response: HTTP 200 OK response with serialized offer data using OfferCreateResponseSerializer.
                     The response includes the updated offer with all its details.
        
        Raises:
            ValidationError: If the input data is invalid (e.g., invalid offer_type,
                           invalid field values, etc.)
            PermissionDenied: If the user is not authenticated or not the owner of the offer
            NotFound: If the offer with the given ID does not exist
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        instance.refresh_from_db()
        response_serializer = OfferCreateResponseSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class OfferDetailView(APIView):
    """
    API view for retrieving a single OfferDetail by ID.
    
    This view provides access to individual offer detail records (basic, standard, premium tiers)
    for authenticated users. Used by the frontend to fetch detailed information about
    specific offer tiers.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OfferDetailSerializer
    
    def get_queryset(self):
        """
        Return queryset containing all OfferDetail objects.
        
        Returns:
            QuerySet: All OfferDetail objects in the database
        """
        return OfferDetail.objects.all()
    
    def get(self, request, pk):
        """
        Retrieve a single OfferDetail by primary key.
        
        Args:
            request: HTTP request object
            pk: Primary key (ID) of the OfferDetail to retrieve
        
        Returns:
            Response: HTTP 200 OK with serialized OfferDetail data, or
                     HTTP 404 NOT FOUND if the OfferDetail does not exist
        """
        try:
            offer_detail = self.get_queryset().get(pk=pk)
            serializer = OfferDetailSerializer(offer_detail)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except OfferDetail.DoesNotExist:
            return Response(
                {'error': 'OfferDetail not found'},
                status=status.HTTP_404_NOT_FOUND
            )
