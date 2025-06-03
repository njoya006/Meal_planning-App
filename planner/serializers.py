# planner/serializers.py

from rest_framework import serializers
from .models import MealPlan, Recipe, NutritionInfo  # Use local Recipe model

class MealPlanSerializer(serializers.ModelSerializer):
    recipe_name = serializers.ReadOnlyField(source='recipe.name')  # optional display

    class Meta:
        model = MealPlan
        fields = ['id', 'user', 'recipe', 'recipe_name', 'date', 'meal_type']
        read_only_fields = ['user']

class NutritionInfoSerializer(serializers.ModelSerializer):
    recipe_name = serializers.ReadOnlyField(source='recipe.name')  # for display

    class Meta:
        model = NutritionInfo
        fields = ['id', 'recipe', 'recipe_name', 'calories', 'protein', 'fat', 'carbs']
