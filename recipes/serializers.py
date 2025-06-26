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
        """Validate and create/get ingredient with smart suggestions."""
        name = data.get('ingredient_name', '').strip()
        if not name:
            raise serializers.ValidationError({'ingredient_name': 'Ingredient name is required.'})
        
        # Clean the name
        clean_name = name.lower()
        
        # Get user from context if available
        user = None
        if hasattr(self, 'context') and 'request' in self.context:
            request = self.context['request']
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user
        
        # First, try exact match (case-insensitive)
        try:
            ingredient = Ingredient.objects.get(name__iexact=clean_name)
            data['ingredient'] = ingredient
            return data
        except Ingredient.DoesNotExist:
            pass
        
        # Try to find similar ingredients for suggestions
        from difflib import get_close_matches
        existing_names = list(Ingredient.objects.values_list('name', flat=True))
        existing_names_lower = [n.lower() for n in existing_names]
        
        close_matches = get_close_matches(clean_name, existing_names_lower, n=3, cutoff=0.7)
        
        if close_matches:
            # Find the original names for the close matches
            suggestions = []
            for match in close_matches:
                original_name = existing_names[existing_names_lower.index(match)]
                suggestions.append(original_name)
            
            # For now, create the ingredient anyway but could show suggestions to frontend
            # In a more advanced implementation, you might want to raise a validation error
            # with suggestions for the frontend to handle
            pass
        
        # Create new ingredient if it doesn't exist
        ingredient, created = Ingredient.objects.get_or_create(
            name__iexact=clean_name,
            defaults={
                'name': name.title(),  # Store with proper capitalization
                'created_by': user,
                'updated_by': user
            }
        )
        
        data['ingredient'] = ingredient
        return data

class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe model."""
    contributor = UserProfileSerializer(read_only=True)
    contributor_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='contributor', write_only=True, required=False)
    ingredients = RecipeIngredientSerializer(source='recipeingredient_set', many=True, read_only=True)
    # Write-only field for ingredient creation
    ingredients_data = RecipeIngredientSerializer(many=True, write_only=True, required=False)
    categories = CategorySerializer(many=True, read_only=True)
    cuisines = CuisineSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    # Accept names instead of IDs for creation
    category_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    cuisine_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    tag_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    # Convert image field to full URL
    image = serializers.SerializerMethodField()
    # Write-only field for image uploads
    image_upload = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'id', 'contributor', 'contributor_id', 'title', 'description', 'instructions',
            'prep_time', 'cook_time', 'servings', 'created_at', 'updated_at', 'ingredients',
            'ingredients_data', 'approved', 'feedback', 'slug', 'is_active', 'difficulty', 'source',
            'categories', 'category_names', 'cuisines', 'cuisine_names', 'tags', 'tag_names', 'image', 'image_upload'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'contributor', 'approved', 'feedback', 'categories', 'cuisines', 'tags']

    def get_image(self, obj):
        """Return the full URL for the recipe image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            else:
                return obj.image.url
        return None

    def to_internal_value(self, data):
        """Override to handle ingredients field mapping."""
        # Map 'ingredients' to 'ingredients_data' for internal processing
        if 'ingredients' in data:
            data = data.copy()  # Don't modify original data
            ingredients_data = data.pop('ingredients')
            data['ingredients_data'] = ingredients_data
        
        return super().to_internal_value(data)

    def _get_objs_by_names(self, model, names):
        objs = []
        for name in names:
            try:
                obj = model.objects.get(name__iexact=name.strip())
                objs.append(obj)
            except model.DoesNotExist:
                raise serializers.ValidationError({f'{model.__name__.lower()}_names': f'No {model.__name__} found with name "{name}".'})
        return objs

    def create(self, validated_data):
        # Extract ingredients data
        ingredients_data = validated_data.pop('ingredients_data', [])
        category_names = validated_data.pop('category_names', [])
        cuisine_names = validated_data.pop('cuisine_names', [])
        tag_names = validated_data.pop('tag_names', [])
        
        # Handle image upload
        image_upload = validated_data.pop('image_upload', None)
        if image_upload:
            validated_data['image'] = image_upload
        
        # Look up objects by name
        categories = self._get_objs_by_names(Category, category_names) if category_names else []
        cuisines = self._get_objs_by_names(Cuisine, cuisine_names) if cuisine_names else []
        tags = self._get_objs_by_names(Tag, tag_names) if tag_names else []
        
        # Create the recipe first
        recipe = Recipe.objects.create(**validated_data)
        
        # Set many-to-many relationships
        if categories:
            recipe.categories.set(categories)
        if cuisines:
            recipe.cuisines.set(cuisines)
        if tags:
            recipe.tags.set(tags)
        
        # Process ingredients with proper context
        ingredient_errors = []
        for i, recipe_ingredient_data in enumerate(ingredients_data):
            # Create individual RecipeIngredient serializer with context
            ingredient_serializer = RecipeIngredientSerializer(
                data=recipe_ingredient_data, 
                context=self.context
            )
            
            if ingredient_serializer.is_valid():
                # The validate method will create/get the ingredient
                validated_ingredient_data = ingredient_serializer.validated_data
                
                ingredient = validated_ingredient_data.pop('ingredient')
                validated_ingredient_data.pop('ingredient_name', None)
                
                # Create the RecipeIngredient relationship
                RecipeIngredient.objects.create(
                    recipe=recipe, 
                    ingredient=ingredient, 
                    **validated_ingredient_data
                )
            else:
                # Collect ingredient validation errors
                ingredient_errors.append(f"Ingredient {i+1}: {ingredient_serializer.errors}")
        
        # If there were ingredient validation errors, raise them
        if ingredient_errors:
            # Delete the recipe since ingredient creation failed
            recipe.delete()
            raise serializers.ValidationError({
                'ingredients': f"Ingredient validation failed: {'; '.join(ingredient_errors)}"
            })
        
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients_data', None)
        category_names = validated_data.pop('category_names', None)
        cuisine_names = validated_data.pop('cuisine_names', None)
        tag_names = validated_data.pop('tag_names', None)
        
        # Handle image upload
        image_upload = validated_data.pop('image_upload', None)
        if image_upload:
            validated_data['image'] = image_upload
        
        # Update basic recipe fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update many-to-many relationships
        if category_names is not None:
            categories = self._get_objs_by_names(Category, category_names)
            instance.categories.set(categories)
        if cuisine_names is not None:
            cuisines = self._get_objs_by_names(Cuisine, cuisine_names)
            instance.cuisines.set(cuisines)
        if tag_names is not None:
            tags = self._get_objs_by_names(Tag, tag_names)
            instance.tags.set(tags)
        
        # Update ingredients
        if ingredients_data is not None:
            # Delete existing ingredient relationships
            instance.recipeingredient_set.all().delete()
            
            # Create new ingredient relationships
            ingredient_errors = []
            for i, recipe_ingredient_data in enumerate(ingredients_data):
                # Create individual RecipeIngredient serializer with context
                ingredient_serializer = RecipeIngredientSerializer(
                    data=recipe_ingredient_data, 
                    context=self.context
                )
                
                if ingredient_serializer.is_valid():
                    # The validate method will create/get the ingredient
                    validated_ingredient_data = ingredient_serializer.validated_data
                    ingredient = validated_ingredient_data.pop('ingredient')
                    validated_ingredient_data.pop('ingredient_name', None)
                    
                    # Create the RecipeIngredient relationship
                    RecipeIngredient.objects.create(
                        recipe=instance, 
                        ingredient=ingredient, 
                        **validated_ingredient_data
                    )
                else:
                    ingredient_errors.append(f"Ingredient {i+1}: {ingredient_serializer.errors}")
            
            # If there were ingredient validation errors, raise them
            if ingredient_errors:
                raise serializers.ValidationError({
                    'ingredients': f"Ingredient validation failed: {'; '.join(ingredient_errors)}"
                })
        
        return instance

    def validate(self, data):
        """Validate recipe data."""
        # Check ingredients from multiple possible sources
        ingredients_data = []
        
        # First try the mapped ingredients_data (from our to_internal_value mapping)
        if 'ingredients_data' in data:
            ingredients_data = data['ingredients_data']
        # Fallback to initial_data for direct frontend calls
        elif hasattr(self, 'initial_data') and 'ingredients' in self.initial_data:
            ingredients_data = self.initial_data['ingredients']
        
        if len(ingredients_data) < 4:
            raise serializers.ValidationError('A recipe must have at least 4 ingredients.')
        
        instructions = data.get('instructions', '')
        if not instructions or len(instructions.strip()) < 20:
            raise serializers.ValidationError('Please provide well-explained steps (at least 20 characters).')
        return data