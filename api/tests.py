from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
import os

class ChefAssistantAPITests(APITestCase):
    def setUp(self):
        # Set a dummy OpenAI key for test environment
        os.environ["OPENAI_API_KEY"] = "sk-test-key"

    def test_no_prompt(self):
        url = reverse("chef-assistant")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("prompt", response.data)

    def test_valid_prompt_mock(self):
        # Patch openai.ChatCompletion.create to avoid real API call
        import openai
        from unittest.mock import patch
        url = reverse("chef-assistant")
        prompt = "I have rice and fish"
        mock_response = type("obj", (object,), {"choices": [type("obj", (object,), {"message": {"content": "You can make fried rice with grilled fish."}})]})
        with patch.object(openai.ChatCompletion, "create", return_value=mock_response):
            response = self.client.post(url, {"prompt": prompt}, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("suggestion", response.data)
            self.assertEqual(response.data["suggestion"], "You can make fried rice with grilled fish.")

    def test_openai_error(self):
        import openai
        from unittest.mock import patch
        url = reverse("chef-assistant")
        prompt = "I have rice and fish"
        with patch.object(openai.ChatCompletion, "create", side_effect=Exception("OpenAI error")):
            response = self.client.post(url, {"prompt": prompt}, format="json")
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn("error", response.data)
