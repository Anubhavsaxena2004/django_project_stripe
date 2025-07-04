from django.contrib import admin
from .models import Prediction, TelegramUser, UserProfile

# Register your models here.
admin.site.register(Prediction)
admin.site.register(TelegramUser)
admin.site.register(UserProfile)
