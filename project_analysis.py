#!/usr/bin/env python
"""
ChopSmo Project Structure Analysis
A comprehensive guide to understand the codebase architecture
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from django.apps import apps
from django.conf import settings
import inspect

def analyze_project_structure():
    """Analyze the overall project structure."""
    print("🏗️  CHOPSMO PROJECT ARCHITECTURE ANALYSIS")
    print("=" * 60)
    
    print("\n📁 PROJECT STRUCTURE:")
    print("""
    chopsmo/
    ├── 📁 meal_project/          # Main Django project
    │   ├── __init__.py
    │   ├── settings.py           # Configuration
    │   ├── urls.py              # Main URL routing
    │   ├── wsgi.py              # Web server interface
    │   ├── asgi.py              # Async server interface
    │   └── csrf_views.py        # CSRF handling
    │
    ├── 📁 recipes/              # Recipe management app
    │   ├── models.py            # Database models
    │   ├── views.py             # API endpoints
    │   ├── serializers.py       # Data serialization
    │   ├── urls.py              # Recipe URLs
    │   ├── admin.py             # Django admin
    │   ├── permissions.py       # Custom permissions
    │   └── management/commands/ # Custom commands
    │
    ├── 📁 users/                # User management app
    │   ├── models.py            # User models
    │   ├── views.py             # User endpoints
    │   ├── serializers.py       # User serialization
    │   └── permissions.py       # User permissions
    │
    ├── 📁 planner/              # Meal planning app
    │   ├── models.py            # Meal plan models
    │   ├── views.py             # Planning endpoints
    │   └── serializers.py       # Plan serialization
    │
    ├── 📁 media/                # User-uploaded files
    │   ├── profile_photos/      # User profile pictures
    │   └── recipes/images/      # Recipe images
    │
    ├── db.sqlite3               # Database file
    ├── manage.py               # Django management
    └── requirements.txt        # Python dependencies
    """)

def analyze_django_apps():
    """Analyze installed Django apps."""
    print("\n🧩 DJANGO APPS ANALYSIS:")
    print("-" * 40)
    
    installed_apps = settings.INSTALLED_APPS
    
    print("\n📦 INSTALLED APPS:")
    for app in installed_apps:
        if app.startswith('django.'):
            print(f"  🔧 {app:<35} (Django built-in)")
        elif app.startswith('rest_framework'):
            print(f"  🌐 {app:<35} (DRF component)")
        else:
            print(f"  📱 {app:<35} (Custom app)")
    
    print(f"\n📊 SUMMARY:")
    print(f"  • Total apps: {len(installed_apps)}")
    print(f"  • Custom apps: {len([app for app in installed_apps if not app.startswith('django.') and not app.startswith('rest_framework')])}")
    print(f"  • Django built-ins: {len([app for app in installed_apps if app.startswith('django.')])}")

def analyze_models():
    """Analyze all models in the project."""
    print("\n🗄️  DATABASE MODELS ANALYSIS:")
    print("-" * 40)
    
    for app_config in apps.get_app_configs():
        if app_config.name in ['recipes', 'users', 'planner']:
            models = app_config.get_models()
            if models:
                print(f"\n📱 {app_config.name.upper()} APP MODELS:")
                for model in models:
                    fields = model._meta.get_fields()
                    print(f"  📋 {model.__name__}")
                    print(f"     • Fields: {len(fields)}")
                    print(f"     • Table: {model._meta.db_table}")
                    
                    # Show key fields
                    key_fields = []
                    for field in fields[:5]:  # Show first 5 fields
                        field_type = type(field).__name__
                        key_fields.append(f"{field.name}({field_type})")
                    
                    if len(fields) > 5:
                        key_fields.append("...")
                    
                    print(f"     • Key fields: {', '.join(key_fields)}")

def analyze_api_endpoints():
    """Analyze API endpoints."""
    print("\n🌐 API ENDPOINTS ANALYSIS:")
    print("-" * 40)
    
    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver
    
    def extract_urls(urlpatterns, prefix=''):
        urls = []
        for pattern in urlpatterns:
            if isinstance(pattern, URLPattern):
                urls.append(prefix + str(pattern.pattern))
            elif isinstance(pattern, URLResolver):
                urls.extend(extract_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
        return urls
    
    resolver = get_resolver()
    all_urls = extract_urls(resolver.url_patterns)
    
    api_urls = [url for url in all_urls if 'api' in url]
    
    print(f"\n🔗 API ENDPOINTS (Found {len(api_urls)}):")
    for url in sorted(api_urls)[:10]:  # Show first 10
        print(f"  📍 /{url}")
    
    if len(api_urls) > 10:
        print(f"  ... and {len(api_urls) - 10} more endpoints")

def analyze_database_stats():
    """Analyze database statistics."""
    print("\n📊 DATABASE STATISTICS:")
    print("-" * 40)
    
    from recipes.models import Recipe, Ingredient, RecipeIngredient, Category, Cuisine, Tag
    from users.models import CustomUser
    from planner.models import MealPlan
    
    stats = {
        'Users': CustomUser.objects.count(),
        'Recipes': Recipe.objects.count(),
        'Ingredients': Ingredient.objects.count(),
        'Recipe-Ingredient Links': RecipeIngredient.objects.count(),
        'Categories': Category.objects.count(),
        'Cuisines': Cuisine.objects.count(),
        'Tags': Tag.objects.count(),
        'Meal Plans': MealPlan.objects.count(),
    }
    
    print("\n📈 CURRENT DATA:")
    for model_name, count in stats.items():
        print(f"  📊 {model_name:<25}: {count:>5} records")
    
    # Recipe statistics
    active_recipes = Recipe.objects.filter(is_active=True).count()
    approved_recipes = Recipe.objects.filter(approved=True).count()
    
    print(f"\n🍽️  RECIPE DETAILS:")
    print(f"  📊 Total recipes:        {stats['Recipes']:>5}")
    print(f"  ✅ Active recipes:       {active_recipes:>5}")
    print(f"  ✅ Approved recipes:     {approved_recipes:>5}")

def analyze_key_features():
    """Analyze key features of the project."""
    print("\n🚀 KEY FEATURES ANALYSIS:")
    print("-" * 40)
    
    print("\n🍽️  RECIPE MANAGEMENT:")
    print("  ✅ Recipe CRUD operations")
    print("  ✅ Ingredient auto-creation")
    print("  ✅ Image upload support")
    print("  ✅ Recipe approval workflow")
    print("  ✅ Categorization (categories, cuisines, tags)")
    print("  ✅ Difficulty levels")
    print("  ✅ Nutrition tracking")
    print("  ✅ Recipe search and filtering")
    
    print("\n👥 USER MANAGEMENT:")
    print("  ✅ Custom user model")
    print("  ✅ Role-based permissions")
    print("  ✅ Profile photos")
    print("  ✅ Regional preferences")
    print("  ✅ Contributor verification")
    
    print("\n📅 MEAL PLANNING:")
    print("  ✅ Meal plan creation")
    print("  ✅ Recipe suggestions")
    print("  ✅ Ingredient-based suggestions")
    
    print("\n🔍 INGREDIENT DISCOVERY:")
    print("  ✅ Ingredient search API")
    print("  ✅ Auto-complete suggestions")
    print("  ✅ Popular ingredients")
    print("  ✅ Regional ingredient support")
    
    print("\n🌐 API FEATURES:")
    print("  ✅ RESTful API with DRF")
    print("  ✅ CORS support for frontend")
    print("  ✅ Image serving with proper headers")
    print("  ✅ Pagination and filtering")
    print("  ✅ Serializer validation")

def analyze_technologies():
    """Analyze technologies used."""
    print("\n🛠️  TECHNOLOGY STACK:")
    print("-" * 40)
    
    print("\n🐍 BACKEND:")
    print("  • Python 3.13")
    print("  • Django (Web framework)")
    print("  • Django REST Framework (API)")
    print("  • SQLite (Database)")
    print("  • Pillow (Image processing)")
    print("  • WhiteNoise (Static files)")
    
    print("\n🌐 API & MIDDLEWARE:")
    print("  • CORS Headers")
    print("  • Custom Media Middleware")
    print("  • CSRF Protection")
    print("  • Authentication & Permissions")
    
    print("\n📁 FILE HANDLING:")
    print("  • Media files (images)")
    print("  • Static files")
    print("  • Custom upload paths")
    
    print("\n🔧 DEVELOPMENT TOOLS:")
    print("  • Django Management Commands")
    print("  • Custom migrations")
    print("  • Debug scripts")
    print("  • Test files")

if __name__ == "__main__":
    analyze_project_structure()
    analyze_django_apps()
    analyze_models()
    analyze_api_endpoints()
    analyze_database_stats()
    analyze_key_features()
    analyze_technologies()
    
    print("\n🎯 NEXT STEPS FOR LEARNING:")
    print("-" * 40)
    print("1. 📖 Study each model in detail")
    print("2. 🔍 Trace API request flow")
    print("3. 🧪 Run test scripts to understand behavior")
    print("4. 📝 Read serializers to understand data flow")
    print("5. 🔒 Understand permissions and authentication")
    print("6. 🌐 Study CORS and middleware")
    print("7. 📊 Practice with Django admin")
    print("8. 🎨 Learn frontend integration patterns")
