import asyncio
import json

from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from channels.db import database_sync_to_async

import django
from django.test import TransactionTestCase, override_settings

from recipes.consumers import LiveChatConsumer
from recipes.models import LiveSession, LiveChatMessage
from django.contrib.auth import get_user_model


# Use an in-memory channel layer for tests to avoid external Redis dependency
CHANNEL_LAYERS_OVERRIDE = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_OVERRIDE)
class LiveChatSmokeTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create(username='smokeuser')
        self.session = LiveSession.objects.create(host=self.user, title='Smoke Live')

    def test_connect_and_chat(self):
        # Use the consumer ASGI app directly but inject an authenticated user into
        # the ASGI scope so persistence requires a real user (no fallback).
        consumer_app = LiveChatConsumer.as_asgi()

        # Simple ASGI wrapper to inject scope['user'] for tests
        def make_scope_user_app(user):
            async def app(scope, receive, send):
                scope['user'] = user
                return await consumer_app(scope, receive, send)
            return app

        application = make_scope_user_app(self.user)

        async def run_test():
            # Connect directly to the consumer and include the real session slug
            communicator = WebsocketCommunicator(application, f"/ws/live/{self.session.slug}/")
            connected, subprotocol = await communicator.connect()
            assert connected

            # Send a chat message
            await communicator.send_json_to({'action': 'chat', 'message': 'hello smoke'})

            # Expect a broadcast back. Presence join/leave messages may arrive first,
            # so loop until we receive a 'chat' action or timeout.
            response = None
            for _ in range(5):
                try:
                    candidate = await communicator.receive_json_from()
                except Exception:
                    candidate = None
                if candidate and candidate.get('action') == 'chat':
                    response = candidate
                    break
                # small pause and try again
                await asyncio.sleep(0.05)

            assert response is not None and response.get('message') == 'hello smoke'

            # Give DB a moment and check persistence (perform DB access on a thread)
            await asyncio.sleep(0.1)
            msgs = await database_sync_to_async(list)(LiveChatMessage.objects.filter(session=self.session))
            assert len(msgs) > 0

            await communicator.disconnect()

        django.setup()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_test())
