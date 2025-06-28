#!/usr/bin/env python
"""
Check admin access and create superuser
"""
import requests

# Test admin access
admin_url = "https://njoya.pythonanywhere.com/admin/"
print(f"🔍 Testing admin access: {admin_url}")

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
print("📋 To create a superuser, run this on your PythonAnywhere console:")
print("cd ~/chopsmo")
print("python manage.py createsuperuser")
print("")
print("Then you can:")
print("1. Log into the admin at: https://njoya.pythonanywhere.com/admin/")
print("2. Create regular users through the admin interface")
print("3. Test login with those users")
print("")
print("Or create a test user directly:")
print('python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username=\'testuser\').delete(); user = User.objects.create_user(\'testuser\', \'testuser@example.com\', \'testpass123\'); print(f\'Created: {user.username} ({user.email})\')"')
