"""Custom permissions for accounts_app API."""
# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from rest_framework import permissions

# 3. Lokale Importe
# (none)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit their objects."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

