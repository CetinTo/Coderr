from django.contrib import admin
from .models import Offer, OfferDetail


class OfferDetailInline(admin.TabularInline):
    """Inline Admin for OfferDetail"""
    model = OfferDetail
    extra = 3


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin for Offer"""
    list_display = ['title', 'creator', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title', 'description', 'creator__username']
    inlines = [OfferDetailInline]


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    """Admin for OfferDetail"""
    list_display = ['offer', 'offer_type', 'title', 'price', 'delivery_time_in_days']
    list_filter = ['offer_type', 'offer__creator']
    search_fields = ['offer__title', 'title']
