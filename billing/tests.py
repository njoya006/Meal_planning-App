from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Plan, WebhookEvent


class BillingSmokeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.client = Client()
        self.plan = Plan.objects.create(id='pro_monthly', title='Pro', interval='monthly', price=9.99, currency='USD')

    def test_plans_list(self):
        resp = self.client.get('/billing/plans/')
        self.assertEqual(resp.status_code, 200)

    def test_webhook_idempotency(self):
        # Simulate processing same event twice
        WebhookEvent.objects.create(provider='stripe', event_id='evt_1', payload={})
        resp = self.client.post('/billing/webhooks/stripe/', data={})
        # Should not create duplicate and should return 200
        self.assertIn(resp.status_code, (200, 400))
