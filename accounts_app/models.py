# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.contrib.auth.models import AbstractUser
from django.db import models

# 3. Lokale Importe
# (none)


class User(AbstractUser):
    """Extended User Model"""
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('business', 'Business'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']
    
    def __str__(self):
        return self.username


class BusinessProfile(models.Model):
    """Profile for Business Users"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='business_profile'
    )
    company_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    working_hours = models.CharField(max_length=100, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Business Profile'
        verbose_name_plural = 'Business Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.company_name} - {self.user.username}"


class CustomerProfile(models.Model):
    """Profile for Customer Users"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    bio = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    location = models.CharField(max_length=255, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - Customer Profile"

