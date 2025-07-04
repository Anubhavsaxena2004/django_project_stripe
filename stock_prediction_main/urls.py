"""
URL configuration for stock_prediction_main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from api.views import DashboardView, LoginTemplateView, RegisterTemplateView, LogoutView, subscribe
from django.conf import settings
from django.conf.urls.static import static

def healthz(request):
    return JsonResponse({
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00Z",
        "service": "stock_prediction_main"
    })

urlpatterns = [
   
    path('', DashboardView.as_view(), name='dashboard'),  # Root URL shows dashboard
    path('login/', LoginTemplateView.as_view(), name='login'),
    path('register/', RegisterTemplateView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('subscribe/', subscribe, name='subscribe'),
    path('api/v1/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('healthz/', healthz, name='healthz'),
    # Healthcheck endpoint to be implemented
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve media files through Django
    from django.views.static import serve
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
