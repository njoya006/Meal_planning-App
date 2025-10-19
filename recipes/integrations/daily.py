"""Daily API helper for live session provisioning."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class DailyAPIError(Exception):
    """Raised when the Daily API returns an error response."""


@dataclass
class DailyClient:
    """Thin HTTP client for Daily REST endpoints."""

    api_key: Optional[str] = None
    base_url: str = "https://api.daily.co/v1"
    timeout: int = 10

    @classmethod
    def from_settings(cls) -> "DailyClient":
        return cls(
            api_key=getattr(settings, "DAILY_API_KEY", None),
            base_url=getattr(settings, "DAILY_BASE_URL", "https://api.daily.co/v1"),
            timeout=int(getattr(settings, "DAILY_TIMEOUT", 10)),
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def create_room(self, *, name: str, privacy: str = "private", properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"name": name, "privacy": privacy}
        if properties:
            payload["properties"] = properties
        return self._post("/rooms", json=payload)

    def create_token(self, *, room_name: str, is_owner: bool = False, user_name: Optional[str] = None, user_id: Optional[str] = None, exp: Optional[int] = None) -> Dict[str, Any]:
        token_props: Dict[str, Any] = {"room_name": room_name, "is_owner": is_owner}
        if user_name:
            token_props["user_name"] = user_name
        if user_id:
            token_props["user_id"] = user_id
        if exp:
            token_props["exp"] = exp
        payload = {"properties": token_props}
        return self._post("/meeting-tokens", json=payload)

    def _post(self, path: str, *, json: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_configured():
            raise DailyAPIError("Daily API key not configured.")
        url = f"{self.base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            resp = requests.post(url, json=json, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:  # pragma: no cover - network failure branch
            logger.exception("Daily API request failed: %s", exc)
            raise DailyAPIError("Unable to reach Daily API.") from exc

        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except ValueError:
                detail = resp.text
            message = f"Daily API error {resp.status_code}: {detail}"
            logger.warning(message)
            raise DailyAPIError(message)

        try:
            return resp.json()
        except ValueError as exc:  # pragma: no cover - unexpected response
            logger.exception("Daily API returned invalid JSON: %s", resp.text)
            raise DailyAPIError("Daily API returned invalid JSON.") from exc
