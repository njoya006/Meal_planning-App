from django.urls import path, include
from rest_framework import routers
from .views import PlanViewSet, create_checkout, purchase_complete, me_subscription, cancel_subscription, stripe_webhook

router = routers.DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/create/', create_checkout, name='checkout-create'),
    path('purchase/complete/', purchase_complete, name='purchase-complete'),
    path('me/subscription/', me_subscription, name='me-subscription'),
    path('subscription/cancel/', cancel_subscription, name='subscription-cancel'),
    path('webhooks/stripe/', stripe_webhook, name='stripe-webhook'),
]
