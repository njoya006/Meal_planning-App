from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg

from .models import FavoriteRecipe, RecipeRating
from .serializers import FavoriteRecipeSerializer, RecipeRatingSerializer
# Assuming 'Recipe' model and permissions from Dev 2 will be available
# from recipes.models import Recipe

class FavoriteRecipeListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteRecipeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteRecipe.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the user can only favorite a recipe once
        recipe_id = self.request.data.get('recipe')
        if FavoriteRecipe.objects.filter(user=self.request.user, recipe_id=recipe_id).exists():
            raise serializer.ValidationError("You have already favorited this recipe.")
        serializer.save(user=self.request.user)
class FavoriteRecipeDestroyView(generics.DestroyAPIView):
    queryset = FavoriteRecipe.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure users can only delete their own favorites
        return FavoriteRecipe.objects.filter(user=self.request.user)

class RecipeRatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RecipeRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # You might want to list ratings for a specific recipe, or all ratings by a user
        recipe_id = self.request.query_params.get('recipe_id')
        if recipe_id:
            return RecipeRating.objects.filter(recipe_id=recipe_id)
        return RecipeRating.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure a user can only rate a recipe once
        recipe_id = self.request.data.get('recipe')
        if RecipeRating.objects.filter(user=self.request.user, recipe_id=recipe_id).exists():
            raise serializer.ValidationError("You have already rated this recipe.")
        serializer.save(user=self.request.user)
class RecipeRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RecipeRating.objects.all()
    serializer_class = RecipeRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure users can only modify/delete their own ratings
        return RecipeRating.objects.filter(user=self.request.user)


