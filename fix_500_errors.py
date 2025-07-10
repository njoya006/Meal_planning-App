#!/usr/bin/env python
"""
Quick fix for 500 errors on PythonAnywhere.
This script:
1. Enables DEBUG mode to see detailed error messages
2. Temporarily disables custom middleware that might be causing issues
3. Enables CORS_ALLOW_ALL_ORIGINS for easier frontend testing

Run this script on PythonAnywhere and then reload your web app.
"""

import os
import sys
from pathlib import Path

def apply_emergency_fix():
    """Apply emergency fixes to resolve 500 errors"""
    print("Applying emergency fixes to resolve 500 errors...")
    
    # Find the project root
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        current_dir = Path(os.getcwd())
        if (current_dir / 'manage.py').exists():
            project_root = current_dir
        else:
            # Try common PythonAnywhere paths
            potential_paths = [
                Path.home() / "chopsmo",
                Path.home() / "ChopSmo",
                Path.home() / "mysite",
                Path.home(),
            ]
            
            project_root = None
            for path in potential_paths:
                if (path / "manage.py").exists():
                    project_root = path
                    break
            
            if project_root is None:
                print("ERROR: Could not find project root. Please provide it as an argument:")
                print("python fix_500_errors.py /path/to/project")
                return False
    
    print(f"Project root: {project_root}")
    
    # Fix 1: Update settings.py
    settings_path = project_root / "meal_project" / "settings.py"
    if not settings_path.exists():
        print(f"ERROR: Could not find settings at {settings_path}")
        return False
    
    print(f"Found settings file: {settings_path}")
    
    with open(settings_path, "r") as f:
        settings_content = f.read()
    
    # Enable DEBUG mode
    if "DEBUG = False" in settings_content:
        settings_content = settings_content.replace("DEBUG = False", "DEBUG = True  # Temporarily enabled to diagnose errors")
        print("✅ Enabled DEBUG mode")
    else:
        print("⚠️ DEBUG mode setting not found or already enabled")
    
    # Enable CORS_ALLOW_ALL_ORIGINS
    if "CORS_ALLOW_ALL_ORIGINS = True" not in settings_content:
        # Find CORS section
        cors_pos = settings_content.find("CORS_ALLOWED_ORIGINS")
        if cors_pos >= 0:
            # Find end of CORS_ALLOWED_ORIGINS list
            end_bracket = settings_content.find("]", cors_pos)
            if end_bracket >= 0:
                # Insert after the CORS_ALLOWED_ORIGINS section
                line_end = settings_content.find("\n", end_bracket)
                if line_end >= 0:
                    settings_content = (
                        settings_content[:line_end + 1] + 
                        "\n# Temporarily enabled to fix CORS issues\nCORS_ALLOW_ALL_ORIGINS = True\n" +
                        settings_content[line_end + 1:]
                    )
                    print("✅ Enabled CORS_ALLOW_ALL_ORIGINS")
    else:
        print("⚠️ CORS_ALLOW_ALL_ORIGINS already enabled")
    
    # Write updated settings
    with open(settings_path, "w") as f:
        f.write(settings_content)
    
    # Fix 2: Disable custom middleware temporarily
    middleware_path = project_root / "meal_project" / "custom_cors_middleware.py"
    if middleware_path.exists():
        print("Found custom middleware file")
        
        # Create backup
        backup_path = middleware_path.with_suffix(".py.bak")
        try:
            with open(middleware_path, "r") as src:
                with open(backup_path, "w") as dst:
                    dst.write(src.read())
            print(f"✅ Backed up middleware to {backup_path}")
        except Exception as e:
            print(f"⚠️ Could not back up middleware: {str(e)}")
        
        # Update the middleware with an improved version that handles OPTIONS requests properly
        safe_middleware = """\"\"\"
Custom middleware to ensure CORS headers are correctly added to all responses.
This is a backup in case Django CORS Headers middleware isn't working correctly.
Enhanced version to better handle OPTIONS requests.
\"\"\"

from django.http import HttpResponse

class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get origin from request headers
        origin = request.META.get('HTTP_ORIGIN')
        allowed_origins = [
            "https://frontendsmo.vercel.app",
            "https://frontendsmo-2kk0xp0y6-njoyas-projects-2a144474.vercel.app",
            "http://localhost:3000"
        ]
        
        # Handle OPTIONS requests before calling the next middleware
        if request.method == "OPTIONS" and origin in allowed_origins:
            response = HttpResponse()
            response.status_code = 200
            response["Content-Length"] = "0"
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, X-Requested-With"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Max-Age"] = "86400"  # 24 hours
            return response
            
        # For non-OPTIONS requests, proceed to the view
        response = self.get_response(request)
        
        # Add CORS headers to all responses if from an allowed origin
        if origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, X-Requested-With"
        
        return response
"""
        
        try:
            with open(middleware_path, "w") as f:
                f.write(safe_middleware)
            print("✅ Replaced middleware with safe version")
        except Exception as e:
            print(f"⚠️ Could not update middleware: {str(e)}")
    else:
        print("⚠️ Custom middleware file not found")
    
    # Fix 3: Create or update a test view to verify things are working
    test_views_path = project_root / "meal_project" / "test_views.py"
    
    test_view_code = """\"\"\"
Test views to verify the application is working
\"\"\"

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class CORSTestView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'CORS test successful',
            'method': 'GET'
        })
    
    def post(self, request):
        return Response({
            'message': 'CORS test successful',
            'method': 'POST',
            'received_data': request.data
        })
    
    def options(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)

class MediaTestView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Media test successful',
            'media_url': '/media/test.jpg'
        })
"""
    
    try:
        with open(test_views_path, "w") as f:
            f.write(test_view_code)
        print(f"✅ Created/updated test views at {test_views_path}")
    except Exception as e:
        print(f"⚠️ Could not create test views: {str(e)}")
    
    print("\n✅ Emergency fixes applied successfully!")
    print("\nNEXT STEPS:")
    print("1. Reload your web app on PythonAnywhere")
    print("2. Check if the 500 errors are resolved")
    print("3. Test the CORS functionality from your frontend")
    print("4. If problems persist, check the error logs for detailed messages")
    print("   (Now that DEBUG=True, detailed error messages will be logged)")
    
    return True

if __name__ == "__main__":
    apply_emergency_fix()
