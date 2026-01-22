"""URL configuration for orders app API."""
from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'orders'

# Router for ViewSet
router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    # Resource-oriented URLs for order counts
    path('orders/business/<int:business_user_id>/count/', views.OrderCountView.as_view(), name='order-count'),
    path('orders/business/<int:business_user_id>/completed-count/', views.CompletedOrderCountView.as_view(), name='completed-order-count'),
    path('order-count/<int:business_user_id>/', views.OrderCountView.as_view(), name='order-count-alt'),
    path('completed-order-count/<int:business_user_id>/', views.CompletedOrderCountView.as_view(), name='completed-order-count-alt'),
]

# Include router URLs
urlpatterns += router.urls

