from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from recipes.consumers import LiveChatConsumer

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/live/<slug:session_slug>/', LiveChatConsumer.as_asgi()),
        ])
    )
})
