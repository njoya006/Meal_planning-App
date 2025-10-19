from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
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
        url = reverse("chef-assistant")
        prompt = "I have rice and fish"
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "You can make fried rice with grilled fish."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch('api.views.chef_assistant.OPENAI_API_KEY', 'sk-test-key'):
            with patch('api.views.chef_assistant.OpenAI') as mock_openai_cls:
                mock_client = MagicMock()
                mock_client.chat.completions.create.return_value = mock_response
                mock_openai_cls.return_value = mock_client
                response = self.client.post(url, {"prompt": prompt}, format="json")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertIn("suggestion", response.data)
                self.assertEqual(response.data["suggestion"], "You can make fried rice with grilled fish.")

    def test_openai_error(self):
        url = reverse("chef-assistant")
        prompt = "I have rice and fish"
        with patch('api.views.chef_assistant.OPENAI_API_KEY', 'sk-test-key'):
            with patch('api.views.chef_assistant.OpenAI') as mock_openai_cls:
                mock_client = MagicMock()
                mock_client.chat.completions.create.side_effect = Exception("OpenAI error")
                mock_openai_cls.return_value = mock_client
                response = self.client.post(url, {"prompt": prompt}, format="json")
                self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
                self.assertIn("error", response.data)
