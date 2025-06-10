# planner/serializers.py

from rest_framework import serializers
from .models import MealPlan, NutritionInfo, DietaryRule  # Use local MealPlan and NutritionInfo models
from recipes.models import Recipe
from users.models import CustomUser

class UserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username']

class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ['id', 'title']

class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer for MealPlan model."""
    user = UserShortSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source='user', write_only=True, required=False)
    recipe = RecipeShortSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all(), source='recipe', write_only=True, required=False)

    class Meta:
        model = MealPlan
        fields = ['id', 'user', 'user_id', 'recipe', 'recipe_id', 'date', 'meal_type', 'created_at']
        read_only_fields = ['id', 'user', 'recipe', 'created_at']

class NutritionInfoSerializer(serializers.ModelSerializer):
    recipe = RecipeShortSerializer(read_only=True)
    recipe_id = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all(), source='recipe', write_only=True, required=False)

    class Meta:
        model = NutritionInfo
        fields = ['id', 'recipe', 'recipe_id', 'calories', 'protein', 'fat', 'carbs', 'fiber', 'sugar', 'sodium', 'cholesterol', 'created_at']
        read_only_fields = ['id', 'recipe', 'created_at']

class DietaryRuleSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), source='user', write_only=True, required=False)

    class Meta:
        model = DietaryRule
        fields = ['id', 'name', 'description', 'include_ingredients', 'exclude_ingredients', 'min_ingredients', 'max_ingredients', 'user', 'user_id', 'priority', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
