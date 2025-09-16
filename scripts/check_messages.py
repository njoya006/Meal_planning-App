import os
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = r"C:\Users\njoya\Desktop\chopsmo"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
import django
django.setup()

from recipes.models import LiveChatMessage

print('LiveChatMessage count:', LiveChatMessage.objects.count())
