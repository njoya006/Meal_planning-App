import asyncio
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.contrib.auth import get_user_model
from django.urls import path

import django
from django.test import TransactionTestCase

from recipes.consumers import LiveChatConsumer
from recipes.models import LiveSession, LiveChatMessage


class LiveChatSmokeTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create(username='smokeuser')
        self.session = LiveSession.objects.create(host=self.user, title='Smoke Live')

    def test_connect_and_chat(self):
        application = URLRouter([path('ws/live/<slug:session_slug>/', LiveChatConsumer.as_asgi())])

        async def run_test():
            communicator = WebsocketCommunicator(application, f"/ws/live/{self.session.slug}/")
            connected, subprotocol = await communicator.connect()
            assert connected

            # Send a chat message
            await communicator.send_json_to({'action': 'chat', 'message': 'hello smoke'})

            # Expect a broadcast back
            response = await communicator.receive_json_from()
            assert response.get('action') == 'chat'
            assert response.get('message') == 'hello smoke'

            # Give DB a moment and check persistence
            await asyncio.sleep(0.1)
            msgs = LiveChatMessage.objects.filter(session=self.session)
            assert msgs.exists()

            await communicator.disconnect()

        django.setup()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_test())