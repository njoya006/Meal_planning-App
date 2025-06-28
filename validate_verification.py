#!/usr/bin/env python
"""
Comprehensive verification system validation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

def validate_verification_system():
    """Validate all components of the verification system."""
    print("🔍 VALIDATING VERIFICATION SYSTEM")
    print("=" * 50)
    
    # Check models
    print("1. Checking models...")
    try:
        from users.models import CustomUser, VerificationApplication
        print("✅ Models imported successfully")
        
        # Check model fields
        user_fields = [f.name for f in CustomUser._meta.fields]
        required_fields = ['verification_status', 'verified_at', 'verified_by']
        
        for field in required_fields:
            if field in user_fields:
                print(f"✅ CustomUser.{field} field exists")
            else:
                print(f"❌ CustomUser.{field} field missing")
        
        # Check VerificationApplication model
        app_fields = [f.name for f in VerificationApplication._meta.fields]
        required_app_fields = ['user', 'full_name', 'cooking_experience', 'status']
        
        for field in required_app_fields:
            if field in app_fields:
                print(f"✅ VerificationApplication.{field} field exists")
            else:
                print(f"❌ VerificationApplication.{field} field missing")
                
    except Exception as e:
        print(f"❌ Model check failed: {e}")
    
    # Check serializers
    print("\n2. Checking serializers...")
    try:
        from users.serializers import (
            VerificationApplicationSerializer,
            VerificationApplicationDetailSerializer,
            VerificationApplicationReviewSerializer
        )
        print("✅ All verification serializers imported successfully")
    except Exception as e:
        print(f"❌ Serializer check failed: {e}")
    
    # Check views
    print("\n3. Checking views...")
    try:
        from users.views import (
            VerificationApplicationView,
            VerificationApplicationListView,
            VerificationApplicationReviewView,
            VerificationStatusView
        )
        print("✅ All verification views imported successfully")
    except Exception as e:
        print(f"❌ View check failed: {e}")
    
    # Check URLs
    print("\n4. Checking URL patterns...")
    try:
        from django.urls import reverse
        from django.test import Client
        
        client = Client()
        
        # Test URL patterns exist
        test_urls = [
            'verification-apply',
            'verification-status', 
            'admin-applications',
        ]
        
        for url_name in test_urls:
            try:
                url = reverse(url_name)
                print(f"✅ URL pattern '{url_name}' exists: {url}")
            except:
                print(f"❌ URL pattern '{url_name}' missing")
                
    except Exception as e:
        print(f"❌ URL check failed: {e}")
    
    # Check notifications
    print("\n5. Checking notification system...")
    try:
        from users.notifications import (
            send_verification_approval_email,
            send_verification_rejection_email
        )
        print("✅ Email notification functions imported successfully")
    except Exception as e:
        print(f"❌ Notification check failed: {e}")
    
    # Check admin
    print("\n6. Checking admin registration...")
    try:
        from django.contrib import admin
        from users.models import VerificationApplication
        
        if VerificationApplication in admin.site._registry:
            print("✅ VerificationApplication registered in admin")
        else:
            print("❌ VerificationApplication not registered in admin")
            
    except Exception as e:
        print(f"❌ Admin check failed: {e}")
    
    print("\n" + "=" * 50)
    print("✅ VERIFICATION SYSTEM VALIDATION COMPLETE")

if __name__ == "__main__":
    validate_verification_system()
