"""URL configuration for reviews app API."""
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reviews'

# Router for ViewSet
router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='review')

urlpatterns = []

# Include router URLs
urlpatterns += router.urls

