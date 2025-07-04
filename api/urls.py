from django.urls import path
from .views import (
    RegisterView, PredictionCreateView, PredictionListView,
    RegisterTemplateView, LoginTemplateView, DashboardView, LogoutView,
    subscribe, stripe_webhook
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Template views (HTML pages)
    path('register/', RegisterTemplateView.as_view(), name='register'),
    path('login/', LoginTemplateView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('subscribe/', subscribe, name='subscribe'),
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
    # API endpoints
    path('register/', RegisterView.as_view(), name='api-register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('predict/', PredictionCreateView.as_view(), name='predict'),
    path('predictions/', PredictionListView.as_view(), name='predictions'),
] 