# This file helps diagnose issues with Django recipe models and migrations

import sqlite3
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

# Import the models
from recipes.models import Recipe, RecipeRating, RecipeComment, RecipeLike

# Print model related names
print("=== Model related names ===")
try:
    for related_obj in Recipe._meta.related_objects:
        if related_obj.related_model == RecipeRating:
            print(f"Recipe -> RecipeRating related_name: {related_obj.name}")
        elif related_obj.related_model == RecipeLike:
            print(f"Recipe -> RecipeLike related_name: {related_obj.name}")
        elif related_obj.related_model == RecipeComment:
            print(f"Recipe -> RecipeComment related_name: {related_obj.name}")
except Exception as e:
    print(f"Error getting Recipe related objects: {e}")
try:
    print(f"RecipeRating -> recipe: {RecipeRating._meta.get_field('recipe').related_name}")
except Exception as e:
    print(f"Error with RecipeRating: {e}")

try:
    print(f"RecipeComment -> recipe: {RecipeComment._meta.get_field('recipe').related_name}")
except Exception as e:
    print(f"Error with RecipeComment: {e}")

try:
    print(f"RecipeLike -> recipe: {RecipeLike._meta.get_field('recipe').related_name}")
except Exception as e:
    print(f"Error with RecipeLike: {e}")

# Check database schema
print("\n=== Database Schema ===")
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check Recipe table
print("\nRecipe table:")
cursor.execute('PRAGMA table_info(recipes_recipe)')
recipe_fields = cursor.fetchall()
for field in recipe_fields:
    print(field)

# Check if relationship tables exist
for table in ['recipes_reciperating', 'recipes_recipelike', 'recipes_recipecomment']:
    print(f"\n{table} exists?")
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    exists = cursor.fetchone()
    print("Yes" if exists else "No")
    
    if exists:
        print(f"{table} schema:")
        cursor.execute(f'PRAGMA table_info({table})')
        table_fields = cursor.fetchall()
        for field in table_fields:
            print(field)

conn.close()

print("\n=== Finished diagnostics ===")
