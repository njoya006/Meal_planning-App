from django.core.management.base import BaseCommand
from recipes.models import Ingredient, IngredientPrice

PRICE_MAP = {
    'rice': 800,
    'cassava': 600,
    'plantain': 400,
    'yam': 500,
    'maize': 450,
    'beans': 700,
    'groundnut': 1200,
    'beef': 2500,
    'chicken': 1800,
    'fish': 2000,
    'palm oil': 1200,
    'vegetable oil': 1200,
    'salt': 200,
    'sugar': 300,
    'tomato': 300,
    'onion': 250,
    'garlic': 800,
    'pepper': 900,
    'eggs': 2000,
}


class Command(BaseCommand):
    help = 'Seed IngredientPrice rows using a default PRICE_MAP for common ingredients.'

    def handle(self, *args, **options):
        created = 0
        for key, price in PRICE_MAP.items():
            # try to find matching ingredient by name contains
            ing = Ingredient.objects.filter(name__icontains=key).first()
            if ing:
                ip, created_flag = IngredientPrice.objects.get_or_create(ingredient=ing, defaults={'price_per_kg': price})
                if created_flag:
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Seeded {created} ingredient prices'))
