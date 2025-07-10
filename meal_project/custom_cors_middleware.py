"""
Custom middleware to ensure CORS headers are correctly added to all responses.
This is a backup in case Django CORS Headers middleware isn't working correctly.
Enhanced version to better handle OPTIONS requests.
"""

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
