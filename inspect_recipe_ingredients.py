#!/usr/bin/env python
"""
Safe database inspection script to check RecipeIngredient data
Run this before making any migrations
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_project.settings')
django.setup()

from recipes.models import RecipeIngredient, Recipe, Ingredient

def inspect_recipe_ingredients():
    """Check the current state of RecipeIngredient data."""
    print("🔍 INSPECTING RECIPEINGREDIENT DATA")
    print("=" * 50)
    
    # Total count
    total_count = RecipeIngredient.objects.count()
    print(f"📊 Total RecipeIngredients: {total_count}")
    
    # Check for null ingredients
    null_ingredients = RecipeIngredient.objects.filter(ingredient__isnull=True)
    null_count = null_ingredients.count()
    print(f"🔍 RecipeIngredients with NULL ingredient: {null_count}")
    
    if null_count > 0:
        print("⚠️  WARNING: Found records with NULL ingredients!")
        print("   These need to be fixed before migration:")
        for ri in null_ingredients[:5]:  # Show first 5
            print(f"   • ID: {ri.id}, Recipe: {ri.recipe.title if ri.recipe else 'No recipe'}")
    else:
        print("✅ No NULL ingredients found - safe to migrate!")
    
    # Check for null recipes
    null_recipes = RecipeIngredient.objects.filter(recipe__isnull=True)
    null_recipe_count = null_recipes.count()
    print(f"🔍 RecipeIngredients with NULL recipe: {null_recipe_count}")
    
    if null_recipe_count > 0:
        print("⚠️  WARNING: Found records with NULL recipes!")
        for ri in null_recipes[:5]:
            print(f"   • ID: {ri.id}, Ingredient: {ri.ingredient.name if ri.ingredient else 'No ingredient'}")
    else:
        print("✅ No NULL recipes found!")
    
    # Show some sample data
    print(f"\n📋 Sample RecipeIngredients:")
    sample_ris = RecipeIngredient.objects.select_related('recipe', 'ingredient')[:5]
    for ri in sample_ris:
        recipe_name = ri.recipe.title if ri.recipe else "NULL"
        ingredient_name = ri.ingredient.name if ri.ingredient else "NULL"
        print(f"   • {recipe_name} -> {ingredient_name} ({ri.quantity} {ri.unit})")

def suggest_fix():
    """Suggest how to fix the issue."""
    print(f"\n🔧 RECOMMENDED FIX:")
    print("=" * 50)
    
    null_ingredients = RecipeIngredient.objects.filter(ingredient__isnull=True)
    null_count = null_ingredients.count()
    
    if null_count > 0:
        print("❌ You have RecipeIngredients with NULL ingredients.")
        print("   Options to fix:")
        print("   1. Delete the invalid records (safest)")
        print("   2. Create a placeholder ingredient for them")
        print("   3. Manually assign proper ingredients")
        print(f"\n   Command to delete invalid records:")
        print(f"   RecipeIngredient.objects.filter(ingredient__isnull=True).delete()")
    else:
        print("✅ Your data looks good!")
        print("   You can safely proceed with migrations.")
        
    print(f"\n🚀 NEXT STEPS:")
    print("1. Fix any data issues shown above")
    print("2. Run: python manage.py makemigrations")
    print("3. Run: python manage.py migrate")

if __name__ == "__main__":
    inspect_recipe_ingredients()
    suggest_fix()
