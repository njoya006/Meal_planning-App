from rest_framework import serializers

from .models import Recipe, Ingredient, RecipeIngredient, Category, Cuisine, Tag
from users.serializers import UserProfileSerializer
from django.conf import settings
from django.contrib.auth import get_user_model

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']

class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    class Meta:
        model = Category
        fields = ['id', 'name']
        read_only_fields = ['id']

class CuisineSerializer(serializers.ModelSerializer):
    """Serializer for Cuisine model."""
    class Meta:
        model = Cuisine
        fields = ['id', 'name']
        read_only_fields = ['id']

class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for RecipeIngredient model."""
    ingredient = IngredientSerializer(read_only=True)
    ingredient_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'ingredient_name', 'quantity', 'unit', 'preparation']

    def validate(self, data):
        name = data.get('ingredient_name', '').strip().lower()
        if not name:
            raise serializers.ValidationError({'ingredient_name': 'Ingredient name is required.'})
        try:
            ingredient = Ingredient.objects.get(name__iexact=name)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError({'ingredient_name': f'Ingredient "{name}" does not exist. Please create it first.'})
        data['ingredient'] = ingredient
        return data

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model."""
    contributor = UserProfileSerializer(read_only=True)
    contributor_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='contributor', write_only=True, required=False)
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, required=False)
    categories = CategorySerializer(many=True, read_only=True)
    cuisines = CuisineSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='categories', many=True, write_only=True, required=False)
    cuisine_ids = serializers.PrimaryKeyRelatedField(queryset=Cuisine.objects.all(), source='cuisines', many=True, write_only=True, required=False)
    tag_ids = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), source='tags', many=True, write_only=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'id', 'contributor', 'contributor_id', 'title', 'description', 'instructions',
            'prep_time', 'cook_time', 'servings', 'created_at', 'updated_at', 'ingredients',
            'approved', 'feedback', 'slug', 'is_active', 'difficulty', 'source',
            'categories', 'category_ids', 'cuisines', 'cuisine_ids', 'tags', 'tag_ids', 'image'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'contributor', 'approved', 'feedback', 'categories', 'cuisines', 'tags']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', [])
        categories = validated_data.pop('categories', []) if 'categories' in validated_data else []
        cuisines = validated_data.pop('cuisines', []) if 'cuisines' in validated_data else []
        tags = validated_data.pop('tags', []) if 'tags' in validated_data else []
        recipe = Recipe.objects.create(**validated_data)
        if categories:
            recipe.categories.set(categories)
        if cuisines:
            recipe.cuisines.set(cuisines)
        if tags:
            recipe.tags.set(tags)
        for recipe_ingredient_data in ingredients_data:
            ingredient = recipe_ingredient_data.pop('ingredient')
            recipe_ingredient_data.pop('ingredient_name', None)
            RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, **recipe_ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipeingredient_set', None)
        categories = validated_data.pop('categories', None)
        cuisines = validated_data.pop('cuisines', None)
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories is not None:
            instance.categories.set(categories)
        if cuisines is not None:
            instance.cuisines.set(cuisines)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients_data is not None:
            instance.recipeingredient_set.all().delete()
            for recipe_ingredient_data in ingredients_data:
                ingredient = recipe_ingredient_data.pop('ingredient')
                recipe_ingredient_data.pop('ingredient_name', None)
                RecipeIngredient.objects.create(recipe=instance, ingredient=ingredient, **recipe_ingredient_data)
        return instance

    def validate(self, data):
        ingredients_data = self.initial_data.get('ingredients', [])
        if len(ingredients_data) < 4:
            raise serializers.ValidationError('A recipe must have at least 4 ingredients.')
        instructions = data.get('instructions', '')
        if not instructions or len(instructions.strip()) < 20:
            raise serializers.ValidationError('Please provide well-explained steps (at least 20 characters).')
        return data