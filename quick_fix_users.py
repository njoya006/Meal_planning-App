#!/usr/bin/env python
# Quick fix for duplicate users on server
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

print("Cleaning up duplicate users...")
User.objects.filter(username='testuser').delete()
User.objects.filter(email='testuser@example.com').delete()
user = User.objects.create_user('testuser', 'testuser@example.com', 'testpass123')
print(f"Created clean user: {user.username} ({user.email})")
print("Done!")
