"""Custom permissions for offers app API."""
# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import permissions

# 3. Lokale Importe
# (none)


class IsOfferOwner(permissions.BasePermission):
    """Permission to only allow offer creators to edit/delete their offers."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the owner of the offer."""
        return obj.creator == request.user


class IsOfferOwnerOrReadOnly(permissions.BasePermission):
    """Permission to allow anyone to read, but only owners to edit/delete."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.creator == request.user


class IsBusinessUser(permissions.BasePermission):
    """Permission to only allow business users."""
    
    def has_permission(self, request, view):
        """Check if user is a business user."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'business'
        )

