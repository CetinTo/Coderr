from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts_app.models import User, BusinessProfile, CustomerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for User"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_superuser']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('user_type',)}),
    )


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    """Admin for BusinessProfile"""
    list_display = ['user', 'company_name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['company_name', 'user__username', 'email']


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Admin for CustomerProfile"""
    list_display = ['user', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'email']

