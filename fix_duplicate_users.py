#!/usr/bin/env python
"""
Fix duplicate user issue causing 500 error
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()

print("🔍 Debugging MultipleObjectsReturned error...")

# Find duplicate usernames
duplicate_usernames = User.objects.values('username').annotate(
    count=Count('username')
).filter(count__gt=1)

print(f"Duplicate usernames: {list(duplicate_usernames)}")

# Find duplicate emails
duplicate_emails = User.objects.values('email').annotate(
    count=Count('email')
).filter(count__gt=1)

print(f"Duplicate emails: {list(duplicate_emails)}")

# Show all users
print("\n📋 All users in database:")
for user in User.objects.all():
    print(f"  ID: {user.id}, Username: '{user.username}', Email: '{user.email}', Active: {user.is_active}")

# Clean up duplicates
print("\n🧹 Cleaning up duplicate users...")

# Remove all testuser accounts and recreate one clean one
testuser_accounts = User.objects.filter(username='testuser')
print(f"Found {testuser_accounts.count()} testuser accounts")
for user in testuser_accounts:
    print(f"  - ID: {user.id}, Email: '{user.email}'")

testuser_accounts.delete()
print("Deleted all testuser accounts")

# Also clean up by email
email_accounts = User.objects.filter(email='testuser@example.com')
print(f"Found {email_accounts.count()} accounts with testuser@example.com")
email_accounts.delete()

# Create one clean test user
print("Creating clean test user...")
user = User.objects.create_user(
    username='testuser',
    email='testuser@example.com',
    password='testpass123'
)
print(f"✅ Created clean test user: ID {user.id}, Username: '{user.username}', Email: '{user.email}'")

print("\n📋 Final user list:")
for user in User.objects.all():
    print(f"  ID: {user.id}, Username: '{user.username}', Email: '{user.email}', Active: {user.is_active}")

print("\n✅ Cleanup complete! MultipleObjectsReturned error should be fixed.")
