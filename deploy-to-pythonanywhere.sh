#!/bin/bash
# This script has been retired now that ChopSmo runs on AWS.
# Use the deployment steps documented in README.md (Certbot, systemd reload, etc.).

echo "⚠️  deploy-to-pythonanywhere.sh has been deprecated."
echo "   The project no longer targets PythonAnywhere hosting."
echo "   Please follow the AWS deployment workflow in README.md instead."
exit 1

# Step 5: Apply any stashed changes if needed
echo "🔍 Checking for stashed changes..."
git stash list

# Step 6: Install any new requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Step 7: First, let's check current settings
echo "🔍 Checking current Django settings..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
print('CSRF_COOKIE_SECURE:', settings.CSRF_COOKIE_SECURE)
"

# Step 8: Check what migrations would be created (SAFE - just shows info)
echo "🔍 Checking what migrations would be created..."
python manage.py makemigrations --dry-run

# Step 9: Create missing migrations (SAFE - only creates files)
echo "🔄 Creating missing migrations..."
python manage.py makemigrations

# Step 10: Show migration plan (SAFE - just shows what will happen)
echo "📋 Showing migration plan..."
python manage.py showmigrations

# Step 11: Apply migrations (SAFE - only adds, doesn't delete)
echo "🗄️ Running database migrations..."
echo "⚠️  This will only ADD new tables/columns, existing data is preserved"
python manage.py migrate

# Step 12: Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Step 13: Create a test user for login testing
echo "👤 Creating test user for login testing..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()

# Check for duplicates first
print('Checking for existing users...')
duplicate_emails = User.objects.values('email').annotate(count=Count('email')).filter(count__gt=1)
if duplicate_emails:
    print(f'⚠️  Found duplicate emails: {list(duplicate_emails)}')

# Clean up any existing test users completely
test_users = User.objects.filter(username='testuser')
if test_users.exists():
    print(f'Removing {test_users.count()} existing testuser accounts...')
    test_users.delete()

email_users = User.objects.filter(email='testuser@example.com')
if email_users.exists():
    print(f'Removing {email_users.count()} accounts with testuser@example.com...')
    email_users.delete()

# Create ONE clean test user
user = User.objects.create_user('testuser', 'testuser@example.com', 'testpass123')
print(f'✅ Created clean test user: {user.username} ({user.email})')
print(f'   ID: {user.id}, Active: {user.is_active}, Password OK: {user.check_password(\"testpass123\")}')

# Verify no duplicates
final_count = User.objects.filter(email='testuser@example.com').count()
if final_count == 1:
    print(f'✅ Verified: Exactly 1 test user exists')
else:
    print(f'❌ Warning: {final_count} users with test email found')
"

# Step 14: Test the login endpoint
echo "🧪 Testing login endpoint with clean test user..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

import requests
import json

# Test CSRF endpoint first
print('Testing CSRF endpoint...')
try:
    response = requests.get('https://njoya.pythonanywhere.com/api/csrf-token/', timeout=10)
    print(f'CSRF Status: {response.status_code}')
    if response.status_code == 200:
        print('✅ CSRF endpoint working')
    else:
        print(f'❌ CSRF failed: {response.text[:100]}')
except Exception as e:
    print(f'❌ CSRF error: {e}')

# Test login endpoint
print('\\nTesting login endpoint...')
try:
    login_data = {'email': 'testuser@example.com', 'password': 'testpass123'}
    response = requests.post(
        'https://njoya.pythonanywhere.com/api/users/login/',
        json=login_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    print(f'Login Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get(\"content-type\")}')
    
    if response.status_code == 200:
        try:
            result = response.json()
            print('✅ Login successful!')
            print(f'   Token: {result.get(\"token\", \"N/A\")[:20]}...')
            print(f'   User ID: {result.get(\"user_id\")}')
            print(f'   Username: {result.get(\"username\")}')
            
            # Test verification endpoints with the token
            token = result.get('token')
            if token:
                print('\\n🔍 Testing verification endpoints...')
                headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
                
                # Test verification status endpoint
                try:
                    status_response = requests.get(
                        'https://njoya.pythonanywhere.com/api/users/verification/status/',
                        headers=headers,
                        timeout=10
                    )
                    print(f'Verification Status Endpoint: {status_response.status_code}')
                    if status_response.status_code == 200:
                        print('✅ Verification status endpoint working')
                        status_data = status_response.json()
                        print(f'   Current status: {status_data.get(\"verification_status\")}')
                        print(f'   Can apply: {status_data.get(\"can_apply\")}')
                        print(f'   Is verified: {status_data.get(\"is_verified\")}')
                        
                        # Test verification apply endpoint (POST)
                        if status_data.get('can_apply'):
                            print('\\n🔄 Testing verification application...')
                            apply_data = {
                                'business_name': 'Test Restaurant',
                                'business_license': 'TEST-LICENSE-123',
                                'description': 'Test verification application from deployment script'
                            }
                            try:
                                apply_response = requests.post(
                                    'https://njoya.pythonanywhere.com/api/users/verification/apply/',
                                    json=apply_data,
                                    headers=headers,
                                    timeout=10
                                )
                                print(f'Apply Endpoint: {apply_response.status_code}')
                                if apply_response.status_code in [200, 201]:
                                    print('✅ Verification application endpoint working')
                                    apply_result = apply_response.json()
                                    print(f'   Application ID: {apply_result.get(\"id\")}')
                                    print(f'   Status: {apply_result.get(\"status\")}')
                                elif apply_response.status_code == 400:
                                    print('✅ Apply endpoint working (already applied or validation error)')
                                    print(f'   Response: {apply_response.json()}')
                                else:
                                    print(f'❌ Apply failed: {apply_response.text[:100]}')
                            except Exception as e:
                                print(f'❌ Apply endpoint error: {e}')
                    else:
                        print(f'❌ Verification status failed: {status_response.text[:100]}')
                except Exception as e:
                    print(f'❌ Verification status error: {e}')
            
        except:
            print(f'❌ Login response not JSON: {response.text[:100]}')
    else:
        print(f'❌ Login failed: {response.text[:200]}')
        
except Exception as e:
    print(f'❌ Login test error: {e}')
"

echo "✅ Deployment complete!"
echo "🔄 Now go to your PythonAnywhere dashboard and click 'Reload' on your web app"
echo ""
echo "🧪 After reload, test these URLs:"
echo "   • https://njoya.pythonanywhere.com/api/csrf-token/"
echo "   • https://njoya.pythonanywhere.com/api/users/login/"
echo "   • https://njoya.pythonanywhere.com/api/users/verification/status/"
echo "   • https://njoya.pythonanywhere.com/admin/"
echo ""
echo "🔑 Test user credentials for login:"
echo "   Email: testuser@example.com"
echo "   Password: testpass123"
echo ""
echo "🌟 NEW VERIFICATION SYSTEM DEPLOYED:"
echo "   • Users can apply for verification at /api/users/verification/apply/"
echo "   • Check verification status at /api/users/verification/status/"
echo "   • Admins can review applications at /api/users/verification/admin/applications/"
echo "   • Email notifications are sent automatically on approval/rejection"
