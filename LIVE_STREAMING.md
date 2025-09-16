Live streaming & realtime chat (MVP)

This project includes an MVP backend for "live cooking" sessions (`LiveSession`) and chat (`LiveChatMessage`). The REST API manages session metadata and permissions, while realtime chat is implemented as a Channels WebSocket consumer at `/ws/live/<session_slug>/`.

Notes to enable locally:
- Install packages: `pip install channels channels-redis`
- Configure `CHANNEL_LAYERS` in `settings.py` (example using Redis):

```py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': { 'hosts': [('127.0.0.1', 6379)], },
    }
}
```

- Use ASGI entrypoint and point your server to `meal_project.asgi.application` (or the top-level `routing.application` if you prefer). Example in `asgi.py` should include `get_asgi_application()` and `ProtocolTypeRouter`.
- For production streaming video, integrate a media server (RTMP or WebRTC).

The current Channel consumer is minimal and intended as a starting point. For scale use Redis channel layer and robust presence/authorization.
