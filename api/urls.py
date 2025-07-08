from django.urls import path
from django.views.generic import TemplateView
from .views import (
    RegisterView, PredictionCreateView, PredictionListView,
    RegisterTemplateView, LoginTemplateView, DashboardView, LogoutView, predictionCreateView1,
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
    path('predictions/json/', TemplateView.as_view(template_name='predictions_json.html'), name='predictions-json'),
    # API endpoints
    path('register/', RegisterView.as_view(), name='api-register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('predict/', PredictionCreateView.as_view(), name='predict'),
    path('predictions/', predictionCreateView1.as_view(), name='api-predictions'),
] 