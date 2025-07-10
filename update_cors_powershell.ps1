# PowerShell Script to update CORS settings for ChopSmo

Write-Host "===== Updating CORS Settings for ChopSmo ====="
Write-Host "This script will update the CORS configuration on the server."

# Create a Python script to apply settings
$script_content = @"
#!/usr/bin/env python
"""
Apply CORS settings for the ChopSmo project.
This script adds explicit CORS headers to Django settings.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meal_project.settings")
import django
django.setup()

print("Applying CORS fixes for ChopSmo...")

# Create or update custom CORS middleware
cors_middleware_path = project_root / 'meal_project' / 'custom_cors_middleware.py'
cors_middleware_content = '''"""
Custom middleware to ensure CORS headers are correctly added to all responses.
This is a backup in case Django CORS Headers middleware isn't working correctly.
"""

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
'''

with open(cors_middleware_path, 'w') as f:
    f.write(cors_middleware_content)
print(f"Created/Updated {cors_middleware_path}")

# Update settings.py to include the custom middleware
settings_path = project_root / 'meal_project' / 'settings.py'
with open(settings_path, 'r') as f:
    settings_content = f.read()

if 'CustomCorsMiddleware' not in settings_content:
    # Add the import if needed
    if 'from .custom_cors_middleware import CustomCorsMiddleware' not in settings_content:
        import_line = "from .custom_cors_middleware import CustomCorsMiddleware\n"
        # Find a good place to add the import - after other imports
        import_section_end = settings_content.find("# Build paths inside the project")
        if import_section_end > 0:
            settings_content = settings_content[:import_section_end] + import_line + settings_content[import_section_end:]
        else:
            # Just add after the docstring
            docstring_end = settings_content.find('"""', 10) + 4  # Skip first """
            settings_content = settings_content[:docstring_end] + "\n" + import_line + settings_content[docstring_end:]
    
    # Add the middleware if needed
    middleware_start = settings_content.find("MIDDLEWARE = [")
    middleware_end = settings_content.find("]", middleware_start) + 1
    
    middleware_section = settings_content[middleware_start:middleware_end]
    new_middleware = "    'meal_project.custom_cors_middleware.CustomCorsMiddleware',\n"
    
    if 'CorsMiddleware' in middleware_section:
        # Add before CorsMiddleware
        cors_pos = middleware_section.find("'corsheaders.middleware.CorsMiddleware'")
        cors_line_start = middleware_section.rfind('\n', 0, cors_pos)
        
        updated_middleware = middleware_section[:cors_line_start + 1] + new_middleware + middleware_section[cors_line_start + 1:]
        settings_content = settings_content[:middleware_start] + updated_middleware + settings_content[middleware_end:]
    
    with open(settings_path, 'w') as f:
        f.write(settings_content)
    print(f"Updated middleware in {settings_path}")

# Update UserLoginView to add explicit CORS headers
from importlib import import_module
try:
    from rest_framework.response import Response
    from rest_framework import status
    
    users_views_path = project_root / 'users' / 'views.py'
    with open(users_views_path, 'r') as f:
        views_content = f.read()
    
    # Check if the view needs modification
    login_view_start = views_content.find('class UserLoginView(APIView)')
    if login_view_start >= 0 and 'Access-Control-Allow-Origin' not in views_content[login_view_start:]:
        # Find the post method
        post_method_start = views_content.find('def post(self, request)', login_view_start)
        if post_method_start >= 0:
            # Find the return Response in post method
            return_pos = views_content.find('return Response({', post_method_start)
            return_end = views_content.find('}, status=status.HTTP_200_OK)', return_pos)
            
            if return_pos >= 0 and return_end >= 0:
                # Replace with modified return with headers
                response_section = views_content[return_pos:return_end+len('}, status=status.HTTP_200_OK)')]
                
                modified_response = '''response = Response({
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
            
            return response'''
                
                views_content = views_content.replace(response_section, modified_response)
                
                # Add options method if it doesn't exist
                if 'def options(self, request' not in views_content[login_view_start:]:
                    # Find the end of the class or the next method
                    next_method = views_content.find('def ', post_method_start + 1)
                    next_class = views_content.find('class ', post_method_start + 1)
                    
                    insertion_point = next_method if next_method >= 0 and (next_class < 0 or next_method < next_class) else next_class
                    
                    if insertion_point >= 0:
                        options_method = '''
    def options(self, request, *args, **kwargs):
        """Handle preflight OPTIONS requests"""
        response = Response(status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "https://frontendsmo.vercel.app"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
'''
                        views_content = views_content[:insertion_point] + options_method + views_content[insertion_point:]
                
                # Write the modified file
                with open(users_views_path, 'w') as f:
                    f.write(views_content)
                print(f"Updated UserLoginView in {users_views_path}")
    
    # Check if django-cors-headers is properly configured
    from django.conf import settings
    
    cors_issues = []
    
    if 'corsheaders' not in settings.INSTALLED_APPS:
        cors_issues.append("'corsheaders' is not in INSTALLED_APPS")
    
    if 'corsheaders.middleware.CorsMiddleware' not in settings.MIDDLEWARE:
        cors_issues.append("'corsheaders.middleware.CorsMiddleware' is not in MIDDLEWARE")
    
    if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
        if 'https://frontendsmo.vercel.app' not in settings.CORS_ALLOWED_ORIGINS:
            cors_issues.append("'https://frontendsmo.vercel.app' is not in CORS_ALLOWED_ORIGINS")
    
    if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
        if 'https://frontendsmo.vercel.app' not in settings.CSRF_TRUSTED_ORIGINS:
            cors_issues.append("'https://frontendsmo.vercel.app' is not in CSRF_TRUSTED_ORIGINS")
    
    if not getattr(settings, 'CORS_ALLOW_CREDENTIALS', False):
        cors_issues.append("CORS_ALLOW_CREDENTIALS is not set to True")
    
    if cors_issues:
        print("\nWARNING: Some CORS settings need attention:")
        for issue in cors_issues:
            print(f" - {issue}")
        print("\nHowever, our custom middleware should override these issues.")
    else:
        print("\nAll standard CORS settings look good!")

except Exception as e:
    print(f"Error updating views: {str(e)}")

print("\nCORS settings update complete!")
"@

# Save the content to a Python script
$script_path = Join-Path $PWD "update_cors.py"
$script_content | Out-File -FilePath $script_path -Encoding utf8

# Run the script
Write-Host "Executing Python script to update CORS settings..."
python $script_path

# Clean up
Remove-Item $script_path

Write-Host "`nDone! Remember to push the changes to your server."
Write-Host "To check if CORS is working properly, run: python check_cors_settings.py"
