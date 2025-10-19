import io
import os
from django.test import Client, TestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile
from recipes.models import Recipe, RecipeImage, InstructionStepImage

User = get_user_model()

@override_settings(MEDIA_ROOT=os.path.join(os.path.dirname(__file__), 'test_media'))
class MultiImageUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='multiimg', password='testpass')
        # Mark as verified contributor
        self.user.is_verified_contributor = True
        self.user.save()
        self.token, _ = Token.objects.get_or_create(user=self.user)

    def _make_test_image(self, name='img.png'):
        # Small 1x1 PNG
        return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82", content_type='image/png')

    def test_multi_image_and_step_image_upload(self):
        url = '/api/recipes/'
        img1 = self._make_test_image('a.png')
        img2 = self._make_test_image('b.png')
        step_img = self._make_test_image('step1.png')

        data = {
            'title': 'Multi Image Test',
            'description': 'Testing multiple images',
            'instructions': '1. Do something\n2. Do next thing',
            'prep_time': 5,
            'cook_time': 5,
            'servings': 1,
            'difficulty': 'easy',
            'ingredients': [
                {'ingredient_name': 'Salt', 'quantity': 1, 'unit': 'tsp'},
                {'ingredient_name': 'Water', 'quantity': 200, 'unit': 'ml'},
                {'ingredient_name': 'Flour', 'quantity': 100, 'unit': 'g'},
                {'ingredient_name': 'Eggs', 'quantity': 2, 'unit': 'piece'},
            ]
        }

        # Build multipart data: image_uploads should be provided as multiple files
        multipart = {
            'title': data['title'],
            'description': data['description'],
            'instructions': data['instructions'],
            'prep_time': data['prep_time'],
            'cook_time': data['cook_time'],
            'servings': data['servings'],
            'difficulty': data['difficulty'],
            'ingredients': '[{"ingredient_name": "Salt", "quantity": 1, "unit": "tsp"}, {"ingredient_name": "Water", "quantity": 200, "unit": "ml"}, {"ingredient_name": "Flour", "quantity": 100, "unit": "g"}, {"ingredient_name": "Eggs", "quantity": 2, "unit": "piece"}]',
            'image_uploads': [img1, img2],
            'step_images_upload': '[{"step_index": 1}]'
        }

        # DRF expects files in 'image_uploads' key; we'll send files separately
        post_data = {
            'title': data['title'],
            'description': data['description'],
            'instructions': data['instructions'],
            'prep_time': data['prep_time'],
            'cook_time': data['cook_time'],
            'servings': data['servings'],
            'difficulty': data['difficulty'],
            'ingredients': multipart['ingredients'],
            'step_images_upload': '[{"step_index": 1, "image": "step1.png"}]'
        }

        # Use files mapping for image_uploads and step image
        files = [
            ('image_uploads', img1),
            ('image_uploads', img2),
            ('step_images_upload', step_img),
        ]

        response = self.client.post(url, data=post_data, files=files, HTTP_AUTHORIZATION=f'Token {self.token.key}')
        # Ensure created
        self.assertEqual(response.status_code, 201, msg=f'Response: {response.content}')
        resp = response.json()
        recipe_id = resp.get('id')
        self.assertIsNotNone(recipe_id)

        # Check that RecipeImage rows were created
        recipe = Recipe.objects.get(pk=recipe_id)
        self.assertEqual(recipe.images.count(), 2)
        self.assertEqual(recipe.step_images.count(), 1)
        ri = recipe.step_images.first()
        self.assertEqual(ri.step_index, 1)

        # Clean up test media
        media_root = os.path.join(os.path.dirname(__file__), 'test_media')
        if os.path.exists(media_root):
            import shutil
            shutil.rmtree(media_root)
