from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Ingredient, Recipe, RecipeIngredient

class IngredientModelTest(TestCase):
    def test_create_ingredient(self):
        ingredient = Ingredient.objects.create(name="Salt")
        self.assertEqual(str(ingredient), "Salt")

class RecipeModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )
        self.ingredient = Ingredient.objects.create(name="Sugar")

    def test_create_recipe(self):
        recipe = Recipe.objects.create(
            contributor=self.user,
            title="Cake",
            description="A simple cake",
            instructions="Mix and bake",
            prep_time=10,
            cook_time=30,
            servings=4
        )
        self.assertEqual(str(recipe), "Cake")
        self.assertEqual(recipe.contributor, self.user)

    def test_add_ingredient_to_recipe(self):
        recipe = Recipe.objects.create(
            contributor=self.user,
            title="Cake",
            description="A simple cake",
            instructions="Mix and bake",
            prep_time=10,
            cook_time=30,
            servings=4
        )
        recipe_ingredient = RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=self.ingredient,
            quantity=2,
            unit="cups"
        )
        self.assertEqual(str(recipe_ingredient), "2 cups of Sugar in Cake")
        self.assertEqual(recipe_ingredient.recipe, recipe)
        self.assertEqual(recipe_ingredient.ingredient, self.ingredient)
