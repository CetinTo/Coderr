"""Custom permissions for orders app API."""
from rest_framework import permissions


class IsOrderOwner(permissions.BasePermission):
    """Permission to only allow order customer to view their orders."""
    
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user


class IsBusinessPartner(permissions.BasePermission):
    """Permission to only allow business partner (offer creator) to update orders."""
    
    def has_object_permission(self, request, view, obj):
        return obj.offer.creator == request.user


class IsBusinessUser(permissions.BasePermission):
    """Permission to only allow business users."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'business'
        )


class IsCustomerUser(permissions.BasePermission):
    """Permission to only allow customer users."""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'customer'
        )


class IsStaff(permissions.BasePermission):
    """Permission to only allow staff/admin users."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsOrderParticipant(permissions.BasePermission):
    """Permission to allow customer or business partner to access order."""
    
    def has_object_permission(self, request, view, obj):
        return (
            obj.customer == request.user or
            obj.offer.creator == request.user
        )

