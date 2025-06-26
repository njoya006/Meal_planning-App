"""
Management command to show current ingredient count and recent ingredients.
Usage: python manage.py show_ingredients
"""

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Recipe, RecipeIngredient


class Command(BaseCommand):
    help = 'Show current ingredients and recent recipe ingredients'

    def handle(self, *args, **options):
        ingredient_count = Ingredient.objects.count()
        recipe_count = Recipe.objects.count()
        
        self.stdout.write(f"📊 Database Status:")
        self.stdout.write(f"   - Total Ingredients: {ingredient_count}")
        self.stdout.write(f"   - Total Recipes: {recipe_count}")
        
        if ingredient_count > 0:
            self.stdout.write(f"\n🥕 Recent Ingredients (last 10):")
            recent_ingredients = Ingredient.objects.order_by('-created_at')[:10]
            for ing in recent_ingredients:
                created_by = ing.created_by.username if ing.created_by else 'System'
                created_at = ing.created_at.strftime('%Y-%m-%d %H:%M') if ing.created_at else 'Unknown'
                self.stdout.write(f"   - {ing.name} (by {created_by} on {created_at})")
        
        if recipe_count > 0:
            self.stdout.write(f"\n🍽️  Recent Recipes with Ingredients:")
            recent_recipes = Recipe.objects.order_by('-created_at')[:5]
            for recipe in recent_recipes:
                ingredients = RecipeIngredient.objects.filter(recipe=recipe)
                ingredient_names = [ri.ingredient.name for ri in ingredients]
                self.stdout.write(f"   - {recipe.title}: {', '.join(ingredient_names)}")
        
        self.stdout.write(f"\n✅ Use the debug tool or create recipes via API to test auto-ingredient creation!")
