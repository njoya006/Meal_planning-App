"""
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
