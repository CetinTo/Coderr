"""Custom permissions for reviews app API."""
# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import permissions

# 3. Lokale Importe
# (none)


class IsReviewOwner(permissions.BasePermission):
    """Permission to only allow review creator (customer) to edit/delete reviews."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the owner of the review."""
        return obj.customer == request.user


class IsCustomerUser(permissions.BasePermission):
    """Permission to only allow customer users."""
    
    def has_permission(self, request, view):
        """Check if user is a customer user."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'customer'
        )

