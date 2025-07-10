#!/usr/bin/env python
"""
Apply CORS fixes on PythonAnywhere
This script is designed to be run on PythonAnywhere to fix CORS issues.

Instructions:
1. Upload this file to your PythonAnywhere account
2. Run it from the PythonAnywhere console: python fix_cors_pythonanywhere.py
3. Reload your web app
"""

import os
import sys
from pathlib import Path

# Path to your project on PythonAnywhere
# Change this to your actual path
project_root = Path(os.path.expanduser("~/ChopSmo"))  # Update this to your actual path

# Create custom CORS middleware file
custom_cors_middleware_path = project_root / "meal_project" / "custom_cors_middleware.py"
custom_cors_middleware_content = """
\"\"\"
Custom middleware to ensure CORS headers are correctly added to all responses.
This is a backup in case Django CORS Headers middleware isn't working correctly.
\"\"\"

class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Call the next middleware or view
        response = self.get_response(request)
        
        # Check if the request is from our frontend
        origin = request.META.get('HTTP_ORIGIN')
        allowed_origins = [
            "https://frontendsmo.vercel.app",
            "http://localhost:3000"
        ]
        
        # Add CORS headers if the request is from an allowed origin
        if origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken"
            
            # Handle preflight OPTIONS requests
            if request.method == "OPTIONS":
                response["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return response
"""

# Modify the UserLoginView to explicitly handle CORS
userlogin_view_code = """
class UserLoginView(APIView):
    permission_classes = []  # AllowAny by default

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user) # Get or create a token for the user
            response = Response({
                'message': 'Login successful.',
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'is_verified_contributor': user.is_verified_contributor
            }, status=status.HTTP_200_OK)
            
            # Add explicit CORS headers
            response["Access-Control-Allow-Origin"] = "https://frontendsmo.vercel.app"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def options(self, request, *args, **kwargs):
        \"\"\"Handle preflight OPTIONS requests\"\"\"
        response = Response(status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "https://frontendsmo.vercel.app"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
"""

def update_settings():
    """Update the settings.py file to use the custom CORS middleware"""
    print("Updating settings.py...")
    
    settings_path = project_root / "meal_project" / "settings.py"
    
    # Read current settings
    with open(settings_path, "r") as f:
        settings_content = f.read()
    
    # Check if already updated
    if "CustomCorsMiddleware" in settings_content:
        print("  - CustomCorsMiddleware already in settings.py")
    else:
        # Add import
        from_import = "from .custom_cors_middleware import CustomCorsMiddleware\n"
        import_pos = settings_content.find("import os")
        if import_pos >= 0:
            settings_content = settings_content[:import_pos] + from_import + settings_content[import_pos:]
        
        # Add middleware to MIDDLEWARE list
        middleware_pos = settings_content.find("MIDDLEWARE = [")
        if middleware_pos >= 0:
            middleware_line_end = settings_content.find("\n", middleware_pos)
            if middleware_line_end >= 0:
                new_middleware = "    'meal_project.custom_cors_middleware.CustomCorsMiddleware',\n"
                settings_content = (settings_content[:middleware_line_end + 1] + 
                                   new_middleware + 
                                   settings_content[middleware_line_end + 1:])
        
        # Write updated settings
        with open(settings_path, "w") as f:
            f.write(settings_content)
        print("  - Updated settings.py with CustomCorsMiddleware")

def update_users_views():
    """Update the users/views.py file to add explicit CORS headers"""
    print("Updating users/views.py...")
    
    views_path = project_root / "users" / "views.py"
    
    # Read current views
    with open(views_path, "r") as f:
        views_content = f.read()
    
    # Check if already updated
    if "Access-Control-Allow-Origin" in views_content:
        print("  - CORS headers already in views.py")
        return
    
    # Find and replace UserLoginView class
    login_view_start = views_content.find("class UserLoginView(APIView)")
    if login_view_start < 0:
        print("  - Could not find UserLoginView class")
        return
    
    # Find next class after UserLoginView
    next_class_start = views_content.find("class ", login_view_start + 10)
    if next_class_start < 0:
        print("  - Could not find end of UserLoginView class")
        return
    
    # Replace the class
    new_views_content = (views_content[:login_view_start] + 
                        userlogin_view_code + 
                        views_content[next_class_start:])
    
    # Write updated views
    with open(views_path, "w") as f:
        f.write(new_views_content)
    print("  - Updated UserLoginView with explicit CORS headers")

def main():
    """Main function to apply all CORS fixes"""
    print("\n=== ChopSmo CORS Fix for PythonAnywhere ===\n")
    
    # Check project path
    if not (project_root / "meal_project" / "settings.py").exists():
        print(f"ERROR: Project not found at {project_root}")
        print("Please update the project_root variable in this script.")
        return
    
    print(f"Project found at: {project_root}\n")
    
    # Create custom CORS middleware file
    with open(custom_cors_middleware_path, "w") as f:
        f.write(custom_cors_middleware_content)
    print(f"Created {custom_cors_middleware_path}")
    
    # Update settings.py
    update_settings()
    
    # Update users/views.py
    update_users_views()
    
    print("\n=== CORS Fix Complete ===")
    print("\nTo apply these changes:")
    print("1. Go to the Web tab in PythonAnywhere")
    print("2. Reload your web app by clicking the green reload button")
    print("3. Test your app from the frontend at https://frontendsmo.vercel.app")

if __name__ == "__main__":
    main()
