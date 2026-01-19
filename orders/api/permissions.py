"""Custom permissions for orders app API."""
# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import permissions

# 3. Lokale Importe
# (none)


class IsOrderOwner(permissions.BasePermission):
    """Permission to only allow order customer to view their orders."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the customer of the order."""
        return obj.customer == request.user


class IsBusinessPartner(permissions.BasePermission):
    """Permission to only allow business partner (offer creator) to update orders."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the business partner (offer creator)."""
        return obj.offer.creator == request.user


class IsBusinessUser(permissions.BasePermission):
    """Permission to only allow business users."""
    
    def has_permission(self, request, view):
        """Check if user is a business user."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'business'
        )


class IsCustomerUser(permissions.BasePermission):
    """Permission to only allow customer users."""
    
    def has_permission(self, request, view):
        """Check if user is a customer user."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'customer'
        )


class IsStaff(permissions.BasePermission):
    """Permission to only allow staff/admin users."""
    
    def has_permission(self, request, view):
        """Check if user is staff."""
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsOrderParticipant(permissions.BasePermission):
    """Permission to allow customer or business partner to access order."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is customer or business partner."""
        return (
            obj.customer == request.user or
            obj.offer.creator == request.user
        )

