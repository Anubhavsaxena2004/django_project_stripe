from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    is_pro = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=128, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    ticker = models.CharField(max_length=10)
    next_day_price = models.FloatField()
    metrics = models.JSONField()
    plot_urls = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticker} - {self.created.date()}"

class TelegramUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chat_id = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return f"{self.user.username} ({self.chat_id})"
