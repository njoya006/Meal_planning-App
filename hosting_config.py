"""Central configuration for remote ChopSmo deployments.

Set the environment variable ``CHOPSMO_PRODUCTION_URL`` to the public URL of the
AWS-hosted backend (currently ``https://api.chopsmo.site``). Override this value
if you later move to a different domain.
Scripts and smoke tests import these constants instead of hard-coding legacy
PythonAnywhere endpoints.
"""
from __future__ import annotations

import os

DEFAULT_PRODUCTION_URL = "https://api.chopsmo.site"

PRODUCTION_BASE_URL = os.environ.get("CHOPSMO_PRODUCTION_URL", DEFAULT_PRODUCTION_URL).rstrip("/")
API_BASE_URL = f"{PRODUCTION_BASE_URL}/api" if PRODUCTION_BASE_URL else ""
ADMIN_URL = f"{PRODUCTION_BASE_URL}/admin/" if PRODUCTION_BASE_URL else ""


def describe_environment() -> str:
    """Return a human-readable summary of the configured remote environment."""
    if "your-aws-hostname" in PRODUCTION_BASE_URL or not PRODUCTION_BASE_URL:
        return (
            "CHOPSMO_PRODUCTION_URL not set. Update hosting_config.py with your AWS "
            "endpoint or export the environment variable before running remote tests."
        )
    return f"Remote backend: {PRODUCTION_BASE_URL} (API root: {API_BASE_URL})"
