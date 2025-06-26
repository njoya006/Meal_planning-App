"""
Custom middleware for serving media files in production with proper CORS headers.
"""
from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils._os import safe_join
from django.views.static import serve
import os


class MediaFilesMiddleware:
    """
    Middleware to serve media files in production when DEBUG=False.
    This is needed for platforms like PythonAnywhere where you can't easily
    configure a separate web server to serve media files.
    Also adds proper CORS headers for cross-origin requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a media file request
        if (request.path.startswith(settings.MEDIA_URL) and 
            not settings.DEBUG):
            
            # Extract the relative path
            relative_path = request.path[len(settings.MEDIA_URL):]
            
            try:
                # Safely join the media root with the relative path
                full_path = safe_join(settings.MEDIA_ROOT, relative_path)
                
                # Check if file exists
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    response = serve(request, relative_path, document_root=settings.MEDIA_ROOT)
                    
                    # Add CORS headers for media files
                    response['Access-Control-Allow-Origin'] = '*'
                    response['Access-Control-Allow-Methods'] = 'GET, HEAD, OPTIONS'
                    response['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept, Authorization'
                    response['Access-Control-Max-Age'] = '86400'
                    
                    # Add cache headers for better performance
                    response['Cache-Control'] = 'public, max-age=31536000'  # 1 year
                    
                    return response
                else:
                    raise Http404("Media file not found")
                    
            except (ValueError, Http404):
                raise Http404("Media file not found")
        
        # Continue with normal request processing
        response = self.get_response(request)
        return response
