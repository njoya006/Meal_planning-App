"""
ASGI config for meal_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')

# Initialize Django
django_asgi_app = get_asgi_application()

# Use Channels ProtocolTypeRouter to combine HTTP and WebSocket handling.
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

# Import consumer after Django is set up
from recipes.consumers import LiveChatConsumer

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/live/<slug:session_slug>/', LiveChatConsumer.as_asgi()),
        ])
    ),
})
