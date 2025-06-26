"""CSRF Token views for frontend integration."""

import json

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods


@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """Get CSRF token for frontend requests."""
    csrf_token = get_token(request)
    return JsonResponse({
        'csrfToken': csrf_token,
        'message': 'CSRF token retrieved successfully'
    })


@csrf_exempt
@require_http_methods(["GET"])
def csrf_debug(request):
    """Debug endpoint to check CSRF configuration."""
    csrf_token = get_token(request)
    
    debug_info = {
        'csrf_token': csrf_token,
        'cookies': dict(request.COOKIES),
        'headers': dict(request.headers),
        'method': request.method,
        'origin': request.headers.get('Origin', 'Not provided'),
        'referer': request.headers.get('Referer', 'Not provided'),
        'user_agent': request.headers.get('User-Agent', 'Not provided'),
        'csrf_cookie_name': 'csrftoken',
        'message': 'CSRF debug information'
    }
    
    response = JsonResponse(debug_info)
    # Ensure CSRF cookie is set
    response.set_cookie(
        'csrftoken', 
        csrf_token, 
        max_age=31449600,  # 1 year
        secure=False,  # Set to True in production
        httponly=False,  # Allow JavaScript access
        samesite='Lax'
    )
    
    return response


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def test_upload_no_csrf(request):
    """Test endpoint for uploads without CSRF (development only)."""
    if request.method == 'OPTIONS':
        response = JsonResponse({'message': 'CORS preflight OK'})
        response["Access-Control-Allow-Origin"] = request.headers.get('Origin', '*')
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response["Access-Control-Allow-Credentials"] = "true"
        return response
    
    try:
        # Handle file upload
        uploaded_file = request.FILES.get('image')
        if uploaded_file:
            return JsonResponse({
                'success': True,
                'message': 'File uploaded successfully (no CSRF)',
                'filename': uploaded_file.name,
                'size': uploaded_file.size,
                'content_type': uploaded_file.content_type
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No file uploaded',
                'files_received': list(request.FILES.keys()),
                'post_data': dict(request.POST)
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Upload failed'
        })
