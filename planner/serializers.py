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
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'image']

class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer for MealPlan model."""
    user = UserShortSerializer(read_only=True)
    recipe = RecipeShortSerializer(read_only=True)

    # Use CharField to accept names instead of IDs
    user_name = serializers.CharField(write_only=True, required=False, source='user.username') # User is set by request.user in perform_create
    recipe_title = serializers.CharField(write_only=True, required=True, source='recipe.title')

    class Meta:
        model = MealPlan
        fields = ['id', 'user', 'user_name', 'recipe', 'recipe_title', 'date', 'meal_type', 'created_at']
        read_only_fields = ['id', 'user', 'recipe', 'created_at']

    def validate(self, data):
        """Ensure either name or ID is provided, and handle name-based retrieval."""
        # Handle recipe_title if provided in the payload
        if 'recipe_title' in data:
            title = data.pop('recipe_title') # Remove to replace with the actual recipe object
            try:
                # Ensure 'recipe' object is set for validated_data
                data['recipe'] = Recipe.objects.get(title__iexact=title) # Case-insensitive match
            except Recipe.DoesNotExist:
                raise serializers.ValidationError({'recipe_title': f"Recipe with title '{title}' not found."})
            except Recipe.MultipleObjectsReturned:
                raise serializers.ValidationError({'recipe_title': f"Multiple recipes found with title '{title}'. Please use a more specific title or ID."})

        # Handle user_name if provided (though frontend is removing it for createMealPlanEntry)
        if 'user_name' in data:
            name = data.pop('user_name') # Remove to replace with the actual user object
            try:
                # This sets 'user' in validated_data if user_name is passed.
                # For new meal plans, perform_create will override this with request.user.
                data['user'] = CustomUser.objects.get(username__iexact=name) # Case-insensitive match
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({'user_name': f"User with username '{name}' not found."})
        
        return data

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        recipe = validated_data.pop('recipe', None)
        # Ensure recipe is a Recipe instance
        if isinstance(recipe, dict):
            recipe_title = recipe.get('title')
            recipe = Recipe.objects.filter(title__iexact=recipe_title).first()
            if not recipe:
                raise serializers.ValidationError({'recipe': f'Recipe with title "{recipe_title}" not found.'})
        meal_plan = MealPlan.objects.create(user=user, recipe=recipe, **validated_data)
        return meal_plan

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
