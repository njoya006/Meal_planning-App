from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from recipes.models import Ingredient, IngredientPrice
from users.models import CustomUser


class IngredientPriceAPITest(APITestCase):
    def setUp(self):
        self.verified = CustomUser.objects.create_user(
            username="verified",
            email="verified@example.com",
            password="testpass123",
        )
        self.verified.is_verified_contributor = True
        self.verified.save(update_fields=["is_verified_contributor"])

        self.staff = CustomUser.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="testpass123",
            is_staff=True,
        )

        self.ingredient = Ingredient.objects.create(name="Plantain", default_unit_weight_g=200)
        IngredientPrice.objects.create(ingredient=self.ingredient, price_per_kg=Decimal("400"))

        self.list_url = reverse("ingredient-price-list")
        self.detail_url = reverse("ingredient-price-detail", args=[self.ingredient.id])

    def tearDown(self):
        # Ensure authentication doesn't leak between tests
        self.client.force_authenticate(user=None)

    def _extract_results(self, response):
        data = response.data
        if isinstance(data, list):
            return data
        return data.get("results", [])

    def test_requires_authentication(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_is_forbidden(self):
        user = CustomUser.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_contributor_can_list_prices(self):
        self.client.force_authenticate(user=self.verified)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        items = self._extract_results(response)
        self.assertTrue(any(item["name"] == "Plantain" for item in items))

    def test_staff_can_update_price_and_weight(self):
        self.client.force_authenticate(user=self.staff)
        payload = {"default_unit_weight_g": 220, "price_per_kg": "450.00"}
        response = self.client.patch(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ingredient.refresh_from_db()
        self.assertEqual(self.ingredient.default_unit_weight_g, 220)
        self.assertEqual(self.ingredient.price.price_per_kg, Decimal("450.00"))

    def test_setting_price_to_null_deletes_record(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(self.detail_url, {"price_per_kg": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(IngredientPrice.objects.filter(ingredient=self.ingredient).exists())

    def test_pagination_limits_page_size(self):
        self.client.force_authenticate(user=self.staff)
        for i in range(60):
            Ingredient.objects.create(name=f"Ingredient {i}")

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 50)
        self.assertEqual(response.data['count'], 61)
        self.assertIsNotNone(response.data['next'])

        response_page_two = self.client.get(f"{self.list_url}?page=2")
        self.assertEqual(response_page_two.status_code, status.HTTP_200_OK)
        self.assertIn('results', response_page_two.data)
        self.assertEqual(len(response_page_two.data['results']), 11)
        self.assertEqual(response_page_two.data['count'], 61)
        self.assertIsNone(response_page_two.data['next'])

    def test_missing_filters_return_expected_ingredients(self):
        self.client.force_authenticate(user=self.staff)
        with_price = Ingredient.objects.create(name="Cassava", default_unit_weight_g=180)
        IngredientPrice.objects.create(ingredient=with_price, price_per_kg=Decimal("550"))

        missing_price = Ingredient.objects.create(name="Okra", default_unit_weight_g=90)
        missing_weight = Ingredient.objects.create(name="Egusi")
        IngredientPrice.objects.create(ingredient=missing_weight, price_per_kg=Decimal("700"))

        response_missing_price = self.client.get(f"{self.list_url}?missing=price")
        self.assertEqual(response_missing_price.status_code, status.HTTP_200_OK)
        names_missing_price = {item["name"] for item in response_missing_price.data["results"]}
        self.assertIn("Okra", names_missing_price)
        self.assertNotIn("Cassava", names_missing_price)

        response_missing_weight = self.client.get(f"{self.list_url}?missing=weight")
        self.assertEqual(response_missing_weight.status_code, status.HTTP_200_OK)
        names_missing_weight = {item["name"] for item in response_missing_weight.data["results"]}
        self.assertIn("Egusi", names_missing_weight)
        self.assertNotIn("Okra", names_missing_weight)

        response_missing_either = self.client.get(f"{self.list_url}?missing=either")
        self.assertEqual(response_missing_either.status_code, status.HTTP_200_OK)
        names_missing_either = {item["name"] for item in response_missing_either.data["results"]}
        self.assertTrue({"Okra", "Egusi"}.issubset(names_missing_either))
        self.assertNotIn("Cassava", names_missing_either)
