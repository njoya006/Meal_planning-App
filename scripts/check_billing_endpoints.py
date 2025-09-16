import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
import django
django.setup()
from django.test import Client

c = Client()
resp1 = c.get('/billing/plans/')
resp2 = c.post('/billing/webhooks/stripe/')
print('GET /billing/plans/ ->', resp1.status_code)
print('POST /billing/webhooks/stripe/ ->', resp2.status_code)
print('Headers for plans response:', dict(resp1.items()))
print('Headers for webhook response:', dict(resp2.items()))
