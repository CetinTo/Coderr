from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order"""
    list_display = ['id', 'customer', 'offer', 'offer_detail', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['customer__username', 'offer__title']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
