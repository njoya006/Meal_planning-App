from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe, RecipeIngredient
from django.urls import reverse


class CameroonSuggestionIntegrationTest(TestCase):
    """Integration-like test for the ingredient-based suggestion endpoint.

    This test creates a user, several ingredients and a recipe that uses them,
    then calls the `suggest-by-ingredients` endpoint to ensure the recipe is returned.
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', email='tester@example.com', password='pass')
        # Mark the test user as a verified contributor so they can call unsafe recipe actions
        try:
            self.user.is_verified_contributor = True
            self.user.save()
        except Exception:
            # Some test user models may not have this field; ignore if absent
            pass

        # Create common Cameroon ingredients
        names = ['Rice', 'Chicken', 'Tomato', 'Onion', 'Palm oil']
        self.ingredients = {}
        for n in names:
            ing = Ingredient.objects.create(name=n)
            self.ingredients[n.lower()] = ing

        # Create a sample recipe that uses these ingredients
        self.recipe = Recipe.objects.create(
            contributor=self.user,
            title='Poulet DG (Test)',
            description='Test recipe for Cameroonian-style chicken and rice.',
            instructions='Mix and cook.\nServe hot.',
            servings=4
        )

        # Attach recipe ingredients
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredients['rice'], quantity=200.0, unit='g')
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredients['chicken'], quantity=500.0, unit='g')
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredients['tomato'], quantity=100.0, unit='g')
        RecipeIngredient.objects.create(recipe=self.recipe, ingredient=self.ingredients['onion'], quantity=50.0, unit='g')

        # Prepare authenticated client using TokenAuthentication to avoid CSRF/session issues
        from rest_framework.authtoken.models import Token
        token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_suggest_by_ingredients_returns_recipe(self):
        payload = {
            'ingredient_names': ['Rice', 'Chicken', 'Tomato', 'Onion']
        }
        # The suggest action is registered on the LiveChatViewSet router as 'live-chat-suggest-by-ingredients'
        url = reverse('live-chat-suggest-by-ingredients')
        resp = self.client.post(url, payload, format='json')
        if resp.status_code != 200:
            body = None
            try:
                body = resp.data
            except Exception:
                body = getattr(resp, 'content', None)
            self.fail(f"Unexpected status code: {resp.status_code} - body: {body}")
        data = resp.data
        self.assertIn('suggested_recipes', data)
        suggested = data['suggested_recipes']
        # There should be at least one suggestion and it should include our recipe
        self.assertTrue(isinstance(suggested, list))
        self.assertGreaterEqual(len(suggested), 1)
        found = False
        for item in suggested:
            r = item.get('recipe')
            if r and r.get('id') == self.recipe.id:
                found = True
                break
        self.assertTrue(found, 'Created recipe not found in suggestions')

