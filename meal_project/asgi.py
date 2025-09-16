"""
ASGI config for meal_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')

# Use Channels ProtocolTypeRouter to combine HTTP and WebSocket handling.
from channels.routing import ProtocolTypeRouter
from routing import application as channels_application

application = ProtocolTypeRouter({
	'http': get_asgi_application(),
	'websocket': channels_application,
})
