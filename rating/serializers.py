from rest_framework import serializers
from .models import FavoriteRecipe, RecipeRating

# Assuming 'RecipeSerializer' will be provided by Dev 2
# from recipes.serializers import RecipeSerializer

class FavoriteRecipeSerializer(serializers.ModelSerializer):
    # This assumes RecipeSerializer will include relevant recipe details
    # recipe = RecipeSerializer(read_only=True) # Uncomment if you want nested recipe data on GET

    class Meta:
        model = FavoriteRecipe
        fields = ['id', 'user', 'recipe', 'created_at']
        read_only_fields = ['user', 'created_at'] # User and creation date are set automatically

class RecipeRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeRating
        fields = ['id', 'user', 'recipe', 'rating', 'created_at']
        read_only_fields = ['user', 'created_at'] # User and creation date are set automatically
