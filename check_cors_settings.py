#!/usr/bin/env python
"""
Check CORS settings for debugging deployment issues.
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

from django.conf import settings

def check_cors_settings():
    """Check the current CORS configuration settings"""
    print("=== CORS Settings Check ===")
    
    print("\nCORS Apps and Middleware:")
    print(f"• corsheaders in INSTALLED_APPS: {'corsheaders' in settings.INSTALLED_APPS}")
    
    middleware_position = -1
    for i, middleware in enumerate(settings.MIDDLEWARE):
        if middleware == 'corsheaders.middleware.CorsMiddleware':
            middleware_position = i
            break
    
    if middleware_position >= 0:
        print(f"• CorsMiddleware found at position {middleware_position}")
        if middleware_position > 0:
            print(f"  Warning: CorsMiddleware should ideally be the first middleware")
    else:
        print("✘ CorsMiddleware not found in MIDDLEWARE!")
    
    print("\nCORS Origin Settings:")
    print(f"• CORS_ALLOW_ALL_ORIGINS: {getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False)}")
    
    allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    print(f"• CORS_ALLOWED_ORIGINS: {len(allowed_origins)} origins")
    for origin in allowed_origins:
        print(f"  - {origin}")
    
    origin_regexes = getattr(settings, 'CORS_ALLOWED_ORIGIN_REGEXES', [])
    print(f"• CORS_ALLOWED_ORIGIN_REGEXES: {len(origin_regexes)} patterns")
    for regex in origin_regexes:
        print(f"  - {regex}")
    
    print("\nCORS Headers and Methods:")
    print(f"• CORS_ALLOW_CREDENTIALS: {getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)}")
    
    allowed_methods = getattr(settings, 'CORS_ALLOW_METHODS', [])
    print(f"• CORS_ALLOW_METHODS: {len(allowed_methods)} methods")
    print(f"  - {', '.join(allowed_methods)}")
    
    allowed_headers = getattr(settings, 'CORS_ALLOW_HEADERS', [])
    print(f"• CORS_ALLOW_HEADERS: {len(allowed_headers)} headers")
    print(f"  - {', '.join(allowed_headers[:5])}{'...' if len(allowed_headers) > 5 else ''}")
    
    print("\n=== Vercel Frontend Check ===")
    vercel_origins = [o for o in allowed_origins if 'vercel.app' in o]
    print(f"• Vercel domains in CORS_ALLOWED_ORIGINS: {len(vercel_origins)}")
    for origin in vercel_origins:
        print(f"  - {origin}")
    
    vercel_regex = any('vercel' in str(r).lower() for r in origin_regexes)
    print(f"• Vercel pattern in CORS_ALLOWED_ORIGIN_REGEXES: {vercel_regex}")
    
    print("\n=== Recommendations ===")
    if not getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False) and not vercel_origins and not vercel_regex:
        print("✘ No Vercel domain found in CORS settings!")
        print("  Add 'https://frontendsmo.vercel.app' to CORS_ALLOWED_ORIGINS")
    
    if 'POST' not in allowed_methods:
        print("✘ POST method not allowed in CORS settings!")
        print("  Add 'POST' to CORS_ALLOW_METHODS")
    
    if 'Authorization' not in [h.lower() for h in allowed_headers]:
        print("✘ 'Authorization' header not allowed in CORS settings!")
        print("  Add 'Authorization' to CORS_ALLOW_HEADERS")
    
    print("\n=== Summary ===")
    if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
        print("✓ CORS_ALLOW_ALL_ORIGINS is True - all origins are allowed (not recommended for production)")
    elif vercel_origins or vercel_regex:
        print("✓ Vercel domains appear to be properly configured in CORS settings")
    else:
        print("✘ Potential CORS issues detected - review recommendations above")

if __name__ == "__main__":
    check_cors_settings()
