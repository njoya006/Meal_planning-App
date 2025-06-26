"""
Management command to populate basic ingredients for testing and production use
"""
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, BasicIngredient


class Command(BaseCommand):
    help = 'Populate basic ingredients for the recipe system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            type=str,
            default='global',
            help='Region for ingredients (global, ng, us, uk, etc.)'
        )
        parser.add_argument(
            '--comprehensive',
            action='store_true',
            help='Add comprehensive ingredient list instead of basic ones'
        )

    def handle(self, *args, **options):
        region = options['region']
        comprehensive = options['comprehensive']
        
        if comprehensive:
            self.add_comprehensive_ingredients(region)
        else:
            self.add_basic_ingredients()

    def add_basic_ingredients(self):
        """Add basic ingredients for testing."""
        basic_ingredients = [
            'Salt', 'Black Pepper', 'Olive Oil', 'Water', 'Sugar', 'Flour', 'Butter',
            'Garlic', 'Onions', 'Vinegar', 'Baking Powder', 'Baking Soda',
            'Soy Sauce', 'Eggs', 'Milk', 'Rice', 'Chicken', 'Beef', 'Pork',
            'Tomatoes', 'Potatoes', 'Carrots', 'Celery', 'Bell Peppers'
        ]
        
        self._create_ingredients(basic_ingredients, 'global')

    def add_comprehensive_ingredients(self, region):
        """Add comprehensive ingredient list."""
        # Common global ingredients
        global_ingredients = [
            # Proteins
            'Chicken', 'Beef', 'Pork', 'Fish', 'Eggs', 'Tofu', 'Beans', 'Lentils',
            'Shrimp', 'Turkey', 'Salmon', 'Tuna', 'Cheese', 'Yogurt', 'Milk',
            
            # Vegetables
            'Onions', 'Garlic', 'Tomatoes', 'Carrots', 'Potatoes', 'Bell Peppers',
            'Spinach', 'Broccoli', 'Lettuce', 'Cucumber', 'Celery', 'Mushrooms',
            'Corn', 'Peas', 'Green Beans', 'Cabbage', 'Cauliflower',
            
            # Grains & Starches
            'Rice', 'Pasta', 'Bread', 'Flour', 'Oats', 'Quinoa', 'Barley',
            'Noodles', 'Couscous', 'Sweet Potatoes',
            
            # Pantry Staples
            'Salt', 'Black Pepper', 'Sugar', 'Honey', 'Olive Oil', 'Vegetable Oil',
            'Butter', 'Vinegar', 'Soy Sauce', 'Garlic Powder', 'Onion Powder',
            'Paprika', 'Cumin', 'Oregano', 'Basil', 'Thyme', 'Rosemary',
            
            # Fruits
            'Apples', 'Bananas', 'Oranges', 'Lemons', 'Limes', 'Strawberries',
            'Blueberries', 'Grapes', 'Avocados', 'Coconut',
            
            # Condiments & Sauces
            'Ketchup', 'Mustard', 'Mayonnaise', 'Hot Sauce', 'Worcestershire Sauce',
            'Baking Powder', 'Baking Soda', 'Vanilla Extract',
        ]
        
        # Nigerian/West African specific ingredients
        nigerian_ingredients = [
            # Proteins
            'Stockfish', 'Dried Fish', 'Snails', 'Goat Meat', 'Chicken',
            'Beef', 'Fish', 'Crayfish', 'Locust Beans',
            
            # Vegetables & Produce
            'Tomatoes', 'Onions', 'Bell Peppers', 'Scotch Bonnet Peppers',
            'Ginger', 'Garlic', 'Scent Leaves', 'Bitter Leaves', 'Pumpkin Leaves',
            'Okra', 'Plantain', 'Yam', 'Cassava', 'Sweet Potatoes', 'Cocoyam',
            
            # Grains & Starches
            'Rice', 'Beans', 'Garri', 'Semolina', 'Yam Flour', 'Plantain Flour',
            'Corn', 'Millet', 'Guinea Corn',
            
            # Spices & Seasonings
            'Palm Oil', 'Groundnut Oil', 'Curry Powder', 'Thyme', 'Bay Leaves',
            'Nutmeg', 'Cloves', 'Ginger Powder', 'Garlic Powder', 'Seasoning Cubes',
            'Salt', 'Black Pepper', 'White Pepper', 'Cameroon Pepper',
            
            # Others
            'Groundnuts', 'Coconut', 'Palm Kernel', 'Ogbono', 'Egusi',
            'Bitter Kola', 'Garden Egg', 'African Spinach',
        ]
        
        # Choose ingredients based on region
        if region == 'ng':  # Nigeria
            ingredients_to_add = nigerian_ingredients
        else:  # Global
            ingredients_to_add = global_ingredients
        
        self._create_ingredients(ingredients_to_add, region)

    def _create_ingredients(self, ingredients_list, region):
        """Create ingredients and basic ingredients."""
        created_count = 0
        existing_count = 0
        
        self.stdout.write(f'Adding {region} ingredients...')
        
        for ingredient_name in ingredients_list:
            # Create or get ingredient
            ingredient, created = Ingredient.objects.get_or_create(
                name__iexact=ingredient_name,
                defaults={
                    'name': ingredient_name,
                    'calories_per_100g': 0,
                    'protein_per_100g': 0,
                    'fat_per_100g': 0,
                    'carbs_per_100g': 0,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'✓ Created: {ingredient_name}')
            else:
                existing_count += 1
            
            # Also add to BasicIngredient for the region
            basic_ingredient, basic_created = BasicIngredient.objects.get_or_create(
                name__iexact=ingredient_name,
                defaults={'name': ingredient_name, 'region': region}
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} new ingredients, '
                f'{existing_count} already existed.'
            )
        )
        
        # Show total counts
        total_ingredients = Ingredient.objects.count()
        total_basic = BasicIngredient.objects.filter(region=region).count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Total ingredients in database: {total_ingredients}\n'
                f'Total basic ingredients for {region}: {total_basic}'
            )
        )
