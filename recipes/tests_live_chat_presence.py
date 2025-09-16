import asyncio

from channels.routing import URLRouter
from django.urls import path

import django
from django.test import TransactionTestCase, override_settings

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from recipes.consumers import LiveChatConsumer
from recipes.models import LiveSession
from django.contrib.auth import get_user_model


# In-memory channel layer for tests
CHANNEL_LAYERS_OVERRIDE = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}


@override_settings(CHANNEL_LAYERS=CHANNEL_LAYERS_OVERRIDE)
class LiveChatPresenceTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.User = get_user_model()
        self.user1 = self.User.objects.create(username='presence1')
        self.user2 = self.User.objects.create(username='presence2')
        self.session = LiveSession.objects.create(host=self.user1, title='Presence Live')

    def _make_wrapped_app(self, user):
        consumer_app = LiveChatConsumer.as_asgi()
        async def app(scope, receive, send):
            scope['user'] = user
            # let the URLRouter set url_route kwargs when used via WebsocketCommunicator
            return await consumer_app(scope, receive, send)
        return app

    def test_presence_and_viewer_count(self):
        application = URLRouter([path('ws/live/<slug:session_slug>/', LiveChatConsumer.as_asgi())])

        async def run_test():
            # Connect user1
            app1 = self._make_wrapped_app(self.user1)
            comm1 = WebsocketCommunicator(app1, f"/ws/live/{self.session.slug}/")
            ok, _ = await comm1.connect()
            assert ok

            # viewer_count should have incremented to 1
            await asyncio.sleep(0.05)
            session = await database_sync_to_async(lambda: LiveSession.objects.get(pk=self.session.pk))()
            assert session.viewer_count == 1

            # Connect user2
            app2 = self._make_wrapped_app(self.user2)
            comm2 = WebsocketCommunicator(app2, f"/ws/live/{self.session.slug}/")
            ok, _ = await comm2.connect()
            assert ok

            await asyncio.sleep(0.05)
            session = await database_sync_to_async(lambda: LiveSession.objects.get(pk=self.session.pk))()
            assert session.viewer_count == 2

            # Disconnect user2
            await comm2.disconnect()
            await asyncio.sleep(0.05)
            session = await database_sync_to_async(lambda: LiveSession.objects.get(pk=self.session.pk))()
            assert session.viewer_count == 1

            # Disconnect user1
            await comm1.disconnect()
            await asyncio.sleep(0.05)
            session = await database_sync_to_async(lambda: LiveSession.objects.get(pk=self.session.pk))()
            assert session.viewer_count == 0

        django.setup()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_test())
