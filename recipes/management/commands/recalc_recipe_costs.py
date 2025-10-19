from django.core.management.base import BaseCommand
from recipes.models import Recipe, RecipeIngredient, Ingredient, IngredientPrice
from django.db import transaction
import decimal


PRICE_MAP = {
    # rough prices in CFA francs per kg (example numbers, adjust as needed)
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
    'eggs': 2000,  # per dozen - handled heuristically
}


def lookup_price_per_kg(name: str) -> decimal.Decimal:
    ln = name.lower()
    # First try IngredientPrice model
    try:
        ip = IngredientPrice.objects.select_related('ingredient').filter(ingredient__name__iexact=name).first()
        if ip:
            return decimal.Decimal(ip.price_per_kg)
    except Exception:
        pass

    for key, price in PRICE_MAP.items():
        if key in ln:
            return decimal.Decimal(price)
    # default price per kg
    return decimal.Decimal(800)


class Command(BaseCommand):
    help = 'Recalculate estimated_cost for recipes based on RecipeIngredient lines.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
        parser.add_argument('--sample', type=int, default=10, help='Show sample of N recipes before applying')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        sample = options['sample']

        qs = Recipe.objects.all().order_by('-id')
        self.stdout.write(f'Processing {qs.count()} recipes')
        shown = 0
        for recipe in qs:
            # sum ingredient costs
            tot = decimal.Decimal(0)
            ris = RecipeIngredient.objects.filter(recipe=recipe).select_related('ingredient')
            for ri in ris:
                # quantity is in grams (g) in our seeder; convert to kg
                qty_kg = decimal.Decimal(ri.quantity) / decimal.Decimal(1000)
                price_per_kg = lookup_price_per_kg(ri.ingredient.name)
                cost = qty_kg * price_per_kg
                tot += cost

            # scale cost for servings (assume quantities for total recipe, so per-serving cost = tot / servings)
            try:
                per_serving = (tot / decimal.Decimal(recipe.servings)) if recipe.servings else tot
            except Exception:
                per_serving = tot

            new_est = per_serving.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_HALF_UP)
            if shown < sample:
                self.stdout.write(f'Recipe {recipe.id}: {recipe.title} | old={recipe.estimated_cost} new={new_est}')
                shown += 1

            if not dry_run:
                try:
                    with transaction.atomic():
                        recipe.estimated_cost = new_est
                        recipe.save(update_fields=['estimated_cost'])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to update {recipe.id}: {e}'))

        self.stdout.write(self.style.SUCCESS('Recalculation complete'))
