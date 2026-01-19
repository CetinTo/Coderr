"""URL configuration for offers app API."""
# 1. Standardbibliothek
# (none)

# 2. Drittanbieter
from django.urls import path
from rest_framework.routers import DefaultRouter

# 3. Lokale Importe
from offers import views

app_name = 'offers'

# Router for ViewSet
router = DefaultRouter()
router.register(r'offers', views.OfferViewSet, basename='offer')

urlpatterns = [
    # Resource-oriented URL for offer details
    path('offers/details/<int:pk>/', views.OfferDetailView.as_view(), name='offer-detail'),
    # Alternative URL for frontend compatibility
    path('offerdetails/<int:pk>/', views.OfferDetailView.as_view(), name='offer-detail-alt'),
]

# Include router URLs
urlpatterns += router.urls

