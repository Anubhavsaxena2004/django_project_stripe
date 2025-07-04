from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils import timezone
from api.models import Prediction, UserProfile

class QuotaMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.path in ['/api/v1/predict/', '/api/v1/predictions/']:
            profile = getattr(request.user, 'userprofile', None)
            if profile and not profile.is_pro:
                today = timezone.now().date()
                count = Prediction.objects.filter(user=request.user, created__date=today).count()
                if count >= 20:
                    return JsonResponse({'error': 'Free tier: 20 predictions/day limit reached. Upgrade to Pro for unlimited predictions.'}, status=429)
        return None 