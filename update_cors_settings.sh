#!/bin/bash
# Script to update CORS settings on PythonAnywhere
# Run this after deploying to make sure CORS is correctly configured

echo "Updating CORS settings for ChopSmo on PythonAnywhere"
echo "==================================================="

# Create a temporary Python script to update settings
cat > update_cors.py << EOL
"""
Update CORS settings for the deployed ChopSmo application.
"""
import os
import sys

# Load Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_project.settings")
import django
django.setup()

from django.conf import settings
import importlib

# Path to the settings module
settings_path = os.path.join(os.path.dirname(settings.__file__), "settings.py")

print(f"Updating settings at: {settings_path}")

# Read the current settings file
with open(settings_path, 'r') as f:
    content = f.read()

# Check if needed settings are present
cors_updates_needed = False

# Check for CORS_ALLOWED_ORIGINS with vercel domain
if "frontendsmo.vercel.app" not in content:
    print("Adding frontendsmo.vercel.app to CORS_ALLOWED_ORIGINS")
    cors_updates_needed = True

# Check for CORS_ALLOWED_ORIGIN_REGEXES
if "CORS_ALLOWED_ORIGIN_REGEXES" not in content:
    print("Adding CORS_ALLOWED_ORIGIN_REGEXES setting")
    cors_updates_needed = True

# Check for CORS_ALLOW_ALL_ORIGINS
if "CORS_ALLOW_ALL_ORIGINS = True" not in content:
    print("Setting CORS_ALLOW_ALL_ORIGINS to True")
    cors_updates_needed = True

# Check if POST is in CORS_ALLOW_METHODS
if "'POST'," not in content and "POST" not in content:
    print("Adding POST method to CORS_ALLOW_METHODS")
    cors_updates_needed = True

if not cors_updates_needed:
    print("All CORS settings already configured correctly!")
    sys.exit(0)

# Update the settings file
with open(settings_path, 'w') as f:
    # Update CORS_ALLOWED_ORIGINS if needed
    if "frontendsmo.vercel.app" not in content:
        content = content.replace(
            "CORS_ALLOWED_ORIGINS = [", 
            'CORS_ALLOWED_ORIGINS = [\n    "https://frontendsmo.vercel.app",'
        )
    
    # Add CORS_ALLOWED_ORIGIN_REGEXES if needed
    if "CORS_ALLOWED_ORIGIN_REGEXES" not in content:
        content = content.replace(
            "CORS_ALLOW_ALL_ORIGINS = True", 
            'CORS_ALLOW_ALL_ORIGINS = True\n\n# Allow requests from any subdomain of vercel.app\nCORS_ALLOWED_ORIGIN_REGEXES = [\n    r"^https://.*\\.vercel\\.app$",\n]'
        )
    
    # Ensure CORS_ALLOW_ALL_ORIGINS is True
    if "CORS_ALLOW_ALL_ORIGINS = True" not in content:
        content = content.replace(
            "# CORS_ALLOW_ALL_ORIGINS = True", 
            "CORS_ALLOW_ALL_ORIGINS = True"
        )
    
    # Ensure POST method is in CORS_ALLOW_METHODS
    if "'POST'," not in content and "POST" not in content:
        content = content.replace(
            "CORS_ALLOW_METHODS = [", 
            "CORS_ALLOW_METHODS = [\n    'POST',"
        )
    
    f.write(content)

print("CORS settings updated successfully!")
print("Please reload your PythonAnywhere web app for changes to take effect.")
EOL

# Execute the script
python update_cors.py

# Clean up
rm update_cors.py

echo ""
echo "To apply these changes, please restart your PythonAnywhere web app:"
echo "1. Go to the Web tab on PythonAnywhere"
echo "2. Click the 'Reload' button for your web app"
echo ""
echo "CORS settings update completed!"
