from django.db import models
from django.conf import settings


class Plan(models.Model):
    """Represents a product plan mapped to a provider price id."""
    id = models.CharField(max_length=64, primary_key=True)
    title = models.CharField(max_length=200)
    interval = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    currency = models.CharField(max_length=8, default='USD')
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)
    recommended = models.BooleanField(default=False)
    trial_days = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.title} ({self.id})"


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subscription_id = models.CharField(max_length=128, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=32)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    entitlements = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Subscription {self.subscription_id} for {self.user}"


class WebhookEvent(models.Model):
    """Track processed webhook events to guarantee idempotency."""
    provider = models.CharField(max_length=64)
    event_id = models.CharField(max_length=128, unique=True)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Webhook {self.provider}:{self.event_id}"
