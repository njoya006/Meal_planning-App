#!/usr/bin/env python
"""
Safe cleanup script for RecipeIngredient data
Only run this after reviewing the inspection results
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from recipes.models import RecipeIngredient, Recipe, Ingredient

def safe_cleanup():
    """Safely clean up invalid RecipeIngredient records."""
    print("🧹 SAFE CLEANUP OF RECIPEINGREDIENT DATA")
    print("=" * 50)
    
    # Check for problems first
    null_ingredients = RecipeIngredient.objects.filter(ingredient__isnull=True)
    null_recipes = RecipeIngredient.objects.filter(recipe__isnull=True)
    
    print(f"Found {null_ingredients.count()} records with NULL ingredient")
    print(f"Found {null_recipes.count()} records with NULL recipe")
    
    if null_ingredients.count() == 0 and null_recipes.count() == 0:
        print("✅ No cleanup needed - data is already clean!")
        return
    
    # Show what would be deleted
    print(f"\n📋 Records that would be cleaned up:")
    problem_records = RecipeIngredient.objects.filter(
        models.Q(ingredient__isnull=True) | models.Q(recipe__isnull=True)
    )
    
    for record in problem_records:
        recipe_name = record.recipe.title if record.recipe else "NULL"
        ingredient_name = record.ingredient.name if record.ingredient else "NULL"
        print(f"   • ID {record.id}: {recipe_name} -> {ingredient_name}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will delete {problem_records.count()} invalid records.")
    print("   Your valid data will NOT be affected.")
    
    confirm = input("Type 'yes' to proceed with cleanup: ")
    
    if confirm.lower() == 'yes':
        deleted_count = problem_records.count()
        problem_records.delete()
        print(f"✅ Cleaned up {deleted_count} invalid records")
        print("🚀 Now you can safely run migrations!")
    else:
        print("❌ Cleanup cancelled")

if __name__ == "__main__":
    from django.db import models
    safe_cleanup()
