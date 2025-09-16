import asyncio
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.test_settings')

import django
from django.core.management import call_command
import pathlib

# Ensure project root is on sys.path so Django settings module can be imported
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    # Enable debug logging for channels/asgiref
    import logging
    logging.basicConfig(level=logging.DEBUG)
    django.setup()
    # Apply migrations to the real dev database so models exist
    call_command('migrate', '--noinput')

    from django.contrib.auth import get_user_model
    from recipes.models import LiveSession, LiveChatMessage
    from channels.testing import WebsocketCommunicator
    from channels.routing import URLRouter
    from django.urls import path
    from recipes.consumers import LiveChatConsumer

    User = get_user_model()
    user, _ = User.objects.get_or_create(username='smokeuser')
    session, _ = LiveSession.objects.get_or_create(host=user, title='Smoke Live')

    application = URLRouter([path('ws/live/<slug:session_slug>/', LiveChatConsumer.as_asgi())])

    async def run_check():
        communicator = WebsocketCommunicator(application, f"/ws/live/{session.slug}/")
        connected, _ = await communicator.connect()
        if not connected:
            print('FAIL: websocket did not connect')
            return 1

        await communicator.send_json_to({'action': 'chat', 'message': 'hello smoke'})
        try:
            response = await communicator.receive_json_from(timeout=5)
        except Exception as exc:
            print('FAIL: did not receive response', exc)
            await communicator.disconnect()
            return 1

        if response.get('action') != 'chat' or response.get('message') != 'hello smoke':
            print('FAIL: unexpected response', response)
            await communicator.disconnect()
            return 1

        # Allow message persistence
        await asyncio.sleep(0.1)
        if not LiveChatMessage.objects.filter(session=session, message__icontains='hello smoke').exists():
            print('FAIL: message not persisted')
            await communicator.disconnect()
            return 1

        await communicator.disconnect()
        print('PASS')
        return 0

    loop = asyncio.new_event_loop()
    try:
        return_code = loop.run_until_complete(run_check())
    finally:
        loop.close()

    sys.exit(return_code)


if __name__ == '__main__':
    main()
