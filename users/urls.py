from django.urls import path
from .views import (
    UserRegistrationView, UserLoginView, UserProfileView, 
    PasswordChangeView, UserListView, UserDetailView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
] 