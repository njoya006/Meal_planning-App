#!/usr/bin/env python
"""
Check what users exist in the database
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("Checking existing users...")
users = User.objects.all()

if not users.exists():
    print("❌ No users found in database!")
    print("\nCreating a test user...")
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    print(f"✅ Created test user: {user.username} ({user.email})")
    print(f"   - Is active: {user.is_active}")
    print(f"   - Password is usable: {user.has_usable_password()}")
else:
    print(f"Found {users.count()} user(s):")
    for user in users:
        print(f"  - Username: {user.username}")
        print(f"    Email: {user.email}")
        print(f"    Is active: {user.is_active}")
        print(f"    Has usable password: {user.has_usable_password()}")
        print(f"    Date joined: {user.date_joined}")
        print(f"    Last login: {user.last_login}")
        print()

print("\nTesting password validation...")
if users.exists():
    test_user = users.first()
    print(f"Testing password for user: {test_user.username}")
    
    # Test various password formats
    test_passwords = ['testpass', 'testpass123', 'password']
    for pwd in test_passwords:
        is_valid = test_user.check_password(pwd)
        print(f"  Password '{pwd}': {'✅ Valid' if is_valid else '❌ Invalid'}")
