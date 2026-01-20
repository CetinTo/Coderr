# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.conf import settings
from django.db import models

# 3. Lokale Importe
from offers.models import Offer, OfferDetail


class Order(models.Model):
    """Order for an offer"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    offer = models.ForeignKey(
        Offer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    offer_detail = models.ForeignKey(
        OfferDetail,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        offer_title = self.offer.title if self.offer else "Deleted Offer"
        return f"Order {self.id} - {offer_title} by {self.customer.username}"
