# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.conf import settings
from django.db import models

# 3. Lokale Importe
# (none)


class Offer(models.Model):
    """Offer from business users"""
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='offers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Offer'
        verbose_name_plural = 'Offers'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    """Details for an offer (Basic, Standard, Premium)"""
    OFFER_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name='details'
    )
    offer_type = models.CharField(max_length=10, choices=OFFER_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_time_in_days = models.IntegerField()
    revisions = models.IntegerField(default=0)
    features = models.JSONField(default=list)
    
    class Meta:
        verbose_name = 'Offer Detail'
        verbose_name_plural = 'Offer Details'
        unique_together = ['offer', 'offer_type']
        ordering = ['offer', 'offer_type']
    
    def __str__(self):
        return f"{self.offer.title} - {self.offer_type}"
