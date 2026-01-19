"""URL configuration for reviews app API."""
# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.urls import path
from rest_framework.routers import DefaultRouter

# 3. Lokale Importe
from reviews import views

app_name = 'reviews'

# Router for ViewSet
router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = []

# Include router URLs
urlpatterns += router.urls

