import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import F
import logging

from .models import LiveSession, LiveChatMessage
from .models import WebsocketToken
import jwt, datetime
from django.utils import timezone

User = get_user_model()
logger = logging.getLogger(__name__)


class LiveChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for live session chat and basic presence.

    Protocol: connect to ws://.../ws/live/<session_slug>/
    - On connect: accept and add user to group
    - On receive: broadcast chat messages to group and persist to DB
    - On disconnect: remove from group
    """

    async def connect(self):
        """Handle new websocket connections: join group, increment viewer count, broadcast join."""
        try:
            # In normal routing the session slug is provided via url_route kwargs.
            # In tests we sometimes call the consumer ASGI app directly (no URLRouter),
            # so url_route may be missing. Fall back to parsing the path.
            try:
                self.session_slug = self.scope['url_route']['kwargs']['session_slug']
            except Exception:
                # Fallback: extract the slug from the path '/ws/live/<slug>/'
                path = self.scope.get('path', '')
                parts = [p for p in path.split('/') if p]
                # Expecting something like ['ws', 'live', '<slug>']
                self.session_slug = parts[2] if len(parts) >= 3 else ''
            self.group_name = f'live_{self.session_slug}'
            logger.debug('LiveChatConsumer.connect: session_slug=%s', self.session_slug)

            # If an ephemeral ws token is provided via ?token= or Authorization header validate it
            # and populate scope['user'] accordingly. This allows mobile clients to connect
            # without a browser session cookie.
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            token = None
            # parse query string for token param
            for part in query_string.split('&'):
                if part.startswith('token='):
                    token = part.split('=', 1)[1]
                    break
            # if Authorization header present, prefer it
            if not token:
                headers = dict((k.decode('utf-8'), v.decode('utf-8')) for k, v in self.scope.get('headers', []))
                auth = headers.get('authorization') or headers.get('Authorization')
                if auth and auth.lower().startswith('bearer '):
                    token = auth.split(' ', 1)[1]

            if token:
                try:
                    secret = getattr(__import__('django.conf').conf.settings, 'SECRET_KEY')
                    payload = jwt.decode(token, secret, algorithms=['HS256'])
                    jti = payload.get('jti')
                    if jti:
                        try:
                            ws_token = WebsocketToken.objects.get(jti=jti, used=False)
                        except WebsocketToken.DoesNotExist:
                            ws_token = None

                        if ws_token:
                            # check expiry
                            if ws_token.expires_at and ws_token.expires_at < timezone.now():
                                logger.debug('LiveChatConsumer.connect: ws token expired')
                            else:
                                # Mark token used and set scope user
                                ws_token.used = True
                                ws_token.save()
                                # populate scope user for downstream code
                                from django.contrib.auth import get_user_model
                                User = get_user_model()
                                try:
                                    user = User.objects.get(pk=payload.get('user_id'))
                                    self.scope['user'] = user
                                except Exception:
                                    pass
                except Exception:
                    logger.exception('LiveChatConsumer.connect: invalid ws token')

            # Add channel to group and accept connection
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            logger.debug('LiveChatConsumer.connect: accepted channel_name=%s', self.channel_name)

            # Increment viewer count in DB and notify group
            logger.debug('LiveChatConsumer.connect: incrementing viewer')
            await database_sync_to_async(self._increment_viewer)()
            await self.channel_layer.group_send(
                self.group_name,
                {'type': 'presence.join', 'username': self._username()}
            )
        except Exception:
            logger.exception('LiveChatConsumer.connect: exception while connecting')
            raise

    async def disconnect(self, close_code):
        """Remove from group and decrement viewer count."""
        logger.debug('LiveChatConsumer.disconnect: channel=%s code=%s', self.channel_name, close_code)
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await database_sync_to_async(self._decrement_viewer)()
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'presence.leave', 'username': self._username()}
        )

    async def receive(self, text_data=None, bytes_data=None):
        """Receive messages from WebSocket, persist chats and broadcast."""
        try:
            if not text_data:
                return
            payload = json.loads(text_data)
            logger.debug('LiveChatConsumer.receive: payload=%s', payload)
            action = payload.get('action')
            if action == 'chat':
                message = payload.get('message', '').strip()
                username = self._username()
                # Persist message in DB
                logger.debug('LiveChatConsumer.receive: saving message for user=%s', username)
                await database_sync_to_async(self._save_message)(username, message)
                # Broadcast to group
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'chat.message',
                        'message': message,
                        'username': username,
                    }
                )
        except Exception:
            logger.exception('LiveChatConsumer.receive: exception while handling message')
            raise

    async def chat_message(self, event):
        logger.debug('LiveChatConsumer.chat_message: event=%s', event)
        await self.send(text_data=json.dumps({
            'action': 'chat',
            'username': event['username'],
            'message': event['message'],
        }))

    async def presence_join(self, event):
        if event.get('username') == self._username():
            return
        await self.send(text_data=json.dumps({'action': 'join', 'username': event.get('username')}))

    async def presence_leave(self, event):
        if event.get('username') == self._username():
            return
        await self.send(text_data=json.dumps({'action': 'leave', 'username': event.get('username')}))

    def _save_message(self, username, message):
        try:
            session = LiveSession.objects.get(slug=self.session_slug)
        except LiveSession.DoesNotExist:
            return
        user = None
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

        if user is None:
            user = getattr(session, 'host', None)
            if user is None:
                logger.debug('LiveChatConsumer._save_message: no user resolved for username=%s, skipping persistence', username)
                return

        logger.debug('LiveChatConsumer._save_message: creating message session=%s user=%s', getattr(session, 'id', None), getattr(user, 'id', None))
        LiveChatMessage.objects.create(session=session, user=user, message=message)

    def _increment_viewer(self):
        """Atomically increment the viewer_count for the session."""
        LiveSession.objects.filter(slug=self.session_slug).update(viewer_count=F('viewer_count') + 1)

    def _decrement_viewer(self):
        """Atomically decrement the viewer_count for the session."""
        LiveSession.objects.filter(slug=self.session_slug).update(viewer_count=F('viewer_count') - 1)

    def _username(self):
        user = self.scope.get('user')
        if user and getattr(user, 'is_authenticated', False):
            return getattr(user, 'username', 'anonymous')
        return 'anonymous'
