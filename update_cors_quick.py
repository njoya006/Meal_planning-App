#!/usr/bin/env python
"""
Script to update CORS settings on PythonAnywhere.
This is a simplified version that only enables CORS_ALLOW_ALL_ORIGINS.

Run this on PythonAnywhere with:
python update_cors_settings.py
"""

import os
import sys
from pathlib import Path

print("Updating CORS settings for ChopSmo...")

# Path to your project on PythonAnywhere
# This is a common path pattern, but you may need to adjust it
project_paths = [
    Path.home() / "ChopSmo",
    Path.home() / "chopsmo",
    Path.home() / "mysite",
    Path.home(),  # Try home directory if nothing else works
]

project_root = None
for path in project_paths:
    if (path / "meal_project" / "settings.py").exists():
        project_root = path
        break

if project_root is None:
    print("Could not find your Django project. Please run this script from your project directory.")
    sys.exit(1)

print(f"Found project at: {project_root}")

# Update settings.py to enable CORS_ALLOW_ALL_ORIGINS
settings_path = project_root / "meal_project" / "settings.py"
with open(settings_path, "r") as f:
    settings_content = f.read()

# Check if CORS_ALLOW_ALL_ORIGINS is already enabled
if "CORS_ALLOW_ALL_ORIGINS = True" in settings_content:
    print("CORS_ALLOW_ALL_ORIGINS is already enabled.")
else:
    # Find the commented out CORS_ALLOW_ALL_ORIGINS line
    cors_comment_pos = settings_content.find("# CORS_ALLOW_ALL_ORIGINS")
    if cors_comment_pos >= 0:
        # Find the line ending
        line_end = settings_content.find("\n", cors_comment_pos)
        if line_end >= 0:
            # Replace the commented line with an enabled one
            new_settings = (
                settings_content[:cors_comment_pos] + 
                "CORS_ALLOW_ALL_ORIGINS = True  # Temporarily enabled for frontend compatibility\n" +
                settings_content[line_end + 1:]
            )
            
            with open(settings_path, "w") as f:
                f.write(new_settings)
            
            print("Updated settings.py: Enabled CORS_ALLOW_ALL_ORIGINS")
    else:
        # If we couldn't find the commented line, add it at the end of the CORS section
        cors_section = settings_content.find("CORS_ALLOWED_ORIGINS")
        if cors_section >= 0:
            # Find the end of the CORS_ALLOWED_ORIGINS list
            cors_end = settings_content.find("]", cors_section)
            if cors_end >= 0:
                # Find the line ending after the closing bracket
                line_end = settings_content.find("\n", cors_end)
                if line_end >= 0:
                    # Add the setting after the CORS_ALLOWED_ORIGINS list
                    new_settings = (
                        settings_content[:line_end + 1] + 
                        "\n# Temporarily enabled for frontend compatibility\nCORS_ALLOW_ALL_ORIGINS = True\n" +
                        settings_content[line_end + 1:]
                    )
                    
                    with open(settings_path, "w") as f:
                        f.write(new_settings)
                    
                    print("Added CORS_ALLOW_ALL_ORIGINS = True to settings.py")

print("\n=== Quick CORS Fix Applied ===")
print("You need to reload your web app for changes to take effect.")
print("To do this, go to the Web tab in PythonAnywhere and click the reload button.")
print("\nRemember: This is a temporary fix and allows ALL origins to access your API.")
print("For better security, you should implement the full CORS solution later.")
