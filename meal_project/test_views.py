"""
CORS and media test views for debugging frontend integration.
"""
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os


class CORSTestView(View):
    """Test view to check CORS configuration."""
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # Add CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept, Authorization, X-CSRFToken'
        response['Access-Control-Max-Age'] = '86400'
        
        return response
    
    def options(self, request, *args, **kwargs):
        """Handle preflight requests."""
        return JsonResponse({'status': 'ok'})
    
    def get(self, request, *args, **kwargs):
        """Test GET request with CORS headers."""
        return JsonResponse({
            'status': 'success',
            'message': 'CORS test successful',
            'media_url': settings.MEDIA_URL,
            'base_url': request.build_absolute_uri('/'),
            'sample_media_urls': [
                request.build_absolute_uri(settings.MEDIA_URL + 'profile_photos/image.png'),
                request.build_absolute_uri(settings.MEDIA_URL + 'profile_photos/image_3GsmtdM.png'),
            ]
        })


class MediaTestView(View):
    """Test view to check media file availability."""
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # Add CORS headers
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Origin, Content-Type, Accept, Authorization'
        
        return response
    
    def get(self, request, *args, **kwargs):
        """Check available media files."""
        media_root = settings.MEDIA_ROOT
        profile_photos_dir = os.path.join(media_root, 'profile_photos')
        
        available_files = []
        if os.path.exists(profile_photos_dir):
            for filename in os.listdir(profile_photos_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    file_url = request.build_absolute_uri(
                        settings.MEDIA_URL + 'profile_photos/' + filename
                    )
                    available_files.append({
                        'filename': filename,
                        'url': file_url,
                        'exists': os.path.exists(os.path.join(profile_photos_dir, filename))
                    })
        
        return JsonResponse({
            'status': 'success',
            'media_root': str(media_root),
            'profile_photos_dir': str(profile_photos_dir),
            'available_files': available_files,
            'total_files': len(available_files)
        })
