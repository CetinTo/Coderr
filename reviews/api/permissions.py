"""Custom permissions for reviews app API."""
from rest_framework import permissions


class IsReviewOwner(permissions.BasePermission):
    """Permission to only allow review creator (customer) to edit/delete reviews."""
    
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user


class IsCustomerUser(permissions.BasePermission):
    """Permission to only allow customer users."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'customer'
        )

