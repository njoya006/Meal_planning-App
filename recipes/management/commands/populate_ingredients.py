"""
Management command to populate basic ingredients for testing
"""
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Populate basic ingredients for testing'

    def handle(self, *args, **options):
        basic_ingredients = [
            'salt', 'pepper', 'oil', 'water', 'sugar', 'flour', 'butter', 
            'garlic', 'onion', 'vinegar', 'baking powder', 'baking soda', 
            'soy sauce', 'eggs', 'milk', 'rice', 'chicken', 'beef', 'pork',
            'tomato', 'potato', 'carrot', 'celery', 'bell pepper'
        ]
        
        created_count = 0
        for ingredient_name in basic_ingredients:
            ingredient, created = Ingredient.objects.get_or_create(
                name=ingredient_name.lower(),
                defaults={
                    'calories_per_100g': 0,
                    'protein_per_100g': 0,
                    'fat_per_100g': 0,
                    'carbs_per_100g': 0,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Created ingredient: {ingredient_name}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} new ingredients. '
                f'Total ingredients: {Ingredient.objects.count()}'
            )
        )
