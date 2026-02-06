"""URL configuration for core project."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API URLs - Include app-specific URLs (resource-oriented)
    path('api/', include('accounts_app.api.urls')),
    path('api/', include('offers.api.urls')),
    path('api/', include('orders.api.urls')),
    path('api/', include('reviews.api.urls')),
]

# Static and Media files for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
