from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from recipes.models import LiveSession


class LiveSessionStatusFilterTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="host", password="pass1234")
        self.base_url = reverse("live-session-list")

    def test_status_live_query_param_matches_various_live_flags(self):
        live_now = LiveSession.objects.create(
            host=self.user,
            title="Currently Live",
            is_live=True,
            started_at=timezone.now(),
        )

        room_only = LiveSession.objects.create(
            host=self.user,
            title="Daily Room Ready",
            external_room_name="room-123",
            external_room_url="https://example.daily/room-123",
        )

        ended = LiveSession.objects.create(
            host=self.user,
            title="Finished",
            is_live=False,
            started_at=timezone.now() - timedelta(hours=1),
            ended_at=timezone.now(),
        )

        response = self.client.get(f"{self.base_url}?status=live")
        self.assertEqual(response.status_code, 200)

        # API returns a paginated JSON list; collect the slugs to verify we see the expected sessions
        slugs = {item["slug"] for item in response.data}
        self.assertIn(live_now.slug, slugs)
        self.assertIn(room_only.slug, slugs)
        self.assertNotIn(ended.slug, slugs)

    def test_status_active_alias_still_supported(self):
        active = LiveSession.objects.create(
            host=self.user,
            title="Active",
            is_live=True,
            started_at=timezone.now(),
        )
        response = self.client.get(f"{self.base_url}?status=active")
        self.assertEqual(response.status_code, 200)
        returned_slugs = {item["slug"] for item in response.data}
        self.assertIn(active.slug, returned_slugs)
