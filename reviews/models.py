# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# 3. Lokale Importe
# (none)


class Review(models.Model):
    """Review of a business user by a customer"""
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    business = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = ['customer', 'business', 'order']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review {self.rating} stars - {self.customer.username} to {self.business.username}"
