#!/usr/bin/env python
"""
Script to create a test user on the PythonAnywhere server
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_user():
    """Create a test user for login testing"""
    username = 'testuser'
    email = 'testuser@example.com'
    password = 'testpass123'
    
    print(f"Creating test user: {username} ({email})")
    
    # Remove existing test user if exists
    User.objects.filter(username=username).delete()
    User.objects.filter(email=email).delete()
    
    # Create new test user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    print(f"✅ Created user successfully!")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Is active: {user.is_active}")
    print(f"   Password set: {user.has_usable_password()}")
    
    # Test password
    if user.check_password(password):
        print(f"   ✅ Password verification successful")
    else:
        print(f"   ❌ Password verification failed")
    
    return user

if __name__ == "__main__":
    create_test_user()
