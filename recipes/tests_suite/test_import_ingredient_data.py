from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from recipes.models import Ingredient, IngredientPrice
import os

class ImportIngredientDataTest(TestCase):
    def setUp(self):
        # ensure a clean state
        Ingredient.objects.all().delete()
        IngredientPrice.objects.all().delete()

    def test_import_creates_ingredient_and_price(self):
        csv = """egg,50,1200
plantain,200,400
"""
        path = os.path.join(os.path.dirname(__file__), 'temp_ing.csv')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(csv)
        out = StringIO()
        call_command('import_ingredient_data', path, '--yes', stdout=out)
        self.assertIn('Applied changes', out.getvalue())
        # verify
        egg = Ingredient.objects.filter(name__iexact='egg').first()
        self.assertIsNotNone(egg)
        self.assertEqual(egg.default_unit_weight_g, 50)
        p = getattr(egg, 'price', None)
        self.assertIsNotNone(p)
        self.assertEqual(p.price_per_kg, 1200)
