"""URL configuration for accounts_app API."""
from django.urls import path
from accounts_app.api import views

app_name = 'accounts_app'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profiles/business/', views.BusinessProfilesView.as_view(), name='business-profiles'),
    path('profiles/customer/', views.CustomerProfilesView.as_view(), name='customer-profiles'),
    path('base-info/', views.BaseInfoView.as_view(), name='base-info'),
]

