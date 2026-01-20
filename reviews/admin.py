from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin for Review"""
    list_display = ['id', 'customer', 'business', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['customer__username', 'business__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
