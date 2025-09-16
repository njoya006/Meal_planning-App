import os
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from .models import WebhookEvent

import stripe

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('price')
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout(request):
    """Create a Stripe Checkout Session and return the URL/session id.

    Expects: {"plan_id": "pro_monthly", "coupon_code": "SUMMER"}
    """
    data = request.data
    plan_id = data.get('plan_id')
    if not plan_id:
        return Response({'code': 'invalid_request', 'message': 'plan_id required'}, status=status.HTTP_400_BAD_REQUEST)

    plan = get_object_or_404(Plan, pk=plan_id)

    # Minimal session creation - backend dev must configure success/cancel URLs
    try:
        session = stripe.checkout.Session.create(
            mode='subscription',
            line_items=[{'price': plan.metadata.get('provider_price_id') or plan.metadata.get('provider_plan_id'), 'quantity': 1}],
            metadata={'user_id': str(request.user.pk), 'plan_id': plan.id},
            success_url=os.getenv('STRIPE_SUCCESS_URL', 'https://frontendsmo.vercel.app/checkout/success?session_id={CHECKOUT_SESSION_ID}'),
            cancel_url=os.getenv('STRIPE_CANCEL_URL', 'https://frontendsmo.vercel.app/checkout/cancel'),
        )
    except Exception as exc:
        return Response({'code': 'provider_error', 'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    return Response({'checkoutUrl': session.url, 'sessionId': session.id})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_complete(request):
    # Optional endpoint to refresh subscription state after returning from checkout
    # The backend should look up session/subscription via provider API and update local records
    user = request.user
    sub = Subscription.objects.filter(user=user).order_by('-created_at').first()
    if not sub:
        return Response({'message': 'no subscription'}, status=status.HTTP_404_NOT_FOUND)
    serializer = SubscriptionSerializer(sub)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_subscription(request):
    sub = Subscription.objects.filter(user=request.user).order_by('-created_at').first()
    if not sub:
        return Response({'subscription': None})
    serializer = SubscriptionSerializer(sub)
    return Response({'subscription': serializer.data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    subscription_id = request.data.get('subscription_id')
    if not subscription_id:
        return Response({'code': 'missing_subscription_id', 'message': 'subscription_id required'}, status=status.HTTP_400_BAD_REQUEST)
    sub = get_object_or_404(Subscription, subscription_id=subscription_id, user=request.user)
    # Backend should call provider to cancel; here we mark cancel_at_period_end
    sub.cancel_at_period_end = True
    sub.status = 'canceled_pending'
    sub.save()
    return Response(SubscriptionSerializer(sub).data)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret) if webhook_secret else stripe.Event.construct_from(request.data, stripe.api_key)
    except Exception as e:
        return Response({'error': str(e)}, status=400)

    # Handle event types - minimal implementation
    # Be defensive: event may be a Stripe object or a plain dict and may lack keys
    typ = event.get('type') if hasattr(event, 'get') else None
    data = None
    try:
        data = event.get('data', {}).get('object') if hasattr(event, 'get') else event['data']['object']
    except Exception:
        data = None

    # If type is missing or payload is malformed, return 400 rather than raising
    if not typ:
        return Response({'error': 'invalid_event', 'message': 'missing event type'}, status=400)

    # Idempotency check
    event_id = event.get('id') if hasattr(event, 'get') else None
    if event_id and WebhookEvent.objects.filter(event_id=event_id).exists():
        return Response({'status': 'already_processed'})

    # Persist the raw event for audit and idempotency when we have an id
    if event_id:
        WebhookEvent.objects.create(provider='stripe', event_id=event_id, payload=event)

    # Process common Stripe events
    if typ == 'checkout.session.completed':
        metadata = data.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        customer = data.get('customer')
        subscription_id = data.get('subscription') or f"sub_{event_id}"
        # Minimal creation: map user by id and create subscription record if not exists
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(pk=int(user_id)) if user_id else None
        except Exception:
            user = None

        plan = None
        if plan_id:
            try:
                plan = Plan.objects.get(pk=plan_id)
            except Plan.DoesNotExist:
                plan = None

        if user:
            Subscription.objects.update_or_create(
                subscription_id=subscription_id,
                defaults={
                    'user': user,
                    'plan': plan,
                    'status': 'active',
                    'entitlements': plan.features if plan else []
                }
            )
    elif typ in ('invoice.payment_succeeded', 'payment_intent.succeeded'):
        # Lookup subscription via invoice/metadata and mark active
        metadata = data.get('metadata', {})
        subscription_id = metadata.get('subscription_id') or data.get('subscription')
        if subscription_id:
            try:
                sub = Subscription.objects.get(subscription_id=subscription_id)
                sub.status = 'active'
                sub.save()
            except Subscription.DoesNotExist:
                pass
    elif typ in ('customer.subscription.updated', 'customer.subscription.created'):
        subscription_id = data.get('id')
        plan_data = data.get('plan') or data.get('items', {}).get('data', [])[0] if data.get('items') else None
        plan_id = None
        if plan_data:
            plan_id = plan_data.get('product') or plan_data.get('price')
        try:
            sub = Subscription.objects.get(subscription_id=subscription_id)
            sub.status = data.get('status', sub.status)
            sub.save()
        except Subscription.DoesNotExist:
            pass
    elif typ in ('invoice.payment_failed',):
        metadata = data.get('metadata', {})
        subscription_id = metadata.get('subscription_id') or data.get('subscription')
        if subscription_id:
            try:
                sub = Subscription.objects.get(subscription_id=subscription_id)
                sub.status = 'past_due'
                sub.save()
            except Subscription.DoesNotExist:
                pass
    return Response({'status': 'ok'})
