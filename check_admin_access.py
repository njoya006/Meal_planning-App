#!/usr/bin/env python
"""Check remote admin availability and outline superuser steps."""
from pathlib import Path
import sys
from urllib.parse import urlparse

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hosting_config import ADMIN_URL, PRODUCTION_BASE_URL, describe_environment

if not ADMIN_URL or "your-aws-hostname" in ADMIN_URL:
    raise RuntimeError(
        "Set CHOPSMO_PRODUCTION_URL or edit hosting_config.py with your AWS admin URL before running this check."
    )

def _get_ssh_host() -> str:
    base = PRODUCTION_BASE_URL or ADMIN_URL
    parsed = urlparse(base)
    return parsed.hostname or "<your-aws-hostname>"


admin_url = ADMIN_URL.rstrip("/") + "/"

print(describe_environment())
print(f"\n🔍 Testing admin access: {admin_url}")

try:
    response = requests.get(admin_url, timeout=10)
    print(f"Admin page status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Admin page accessible")
        if "Django Administration" in response.text:
            print("✅ Django admin is working")
        else:
            print("❌ Unexpected admin page content")
    else:
        print(f"❌ Admin page failed: {response.status_code}")
except Exception as e:
    print(f"❌ Admin request failed: {e}")

print("\n" + "="*50)
print("📋 To create a superuser on your AWS instance:")
ssh_host = _get_ssh_host()
print(f"ssh ubuntu@{ssh_host}")
print("cd ~/chopsmo")
print("source venv/bin/activate")
print("python manage.py createsuperuser")
print("")
print("Then you can:")
print(f"1. Log into the admin at: {admin_url}")
print("2. Create regular users through the admin interface")
print("3. Test login with those users")
print("")
print("Or create a test user directly:")
print('python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username=\'testuser\').delete(); user = User.objects.create_user(\'testuser\', \'testuser@example.com\', \'testpass123\'); print(f\'Created: {user.username} ({user.email})\')"')
