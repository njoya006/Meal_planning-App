from rest_framework import serializers
import json

from .models import Recipe, Ingredient, RecipeIngredient, Category, Cuisine, Tag, RecipeRating, RecipeLike, RecipeComment, IngredientPrice
from .models import RecipeImage, InstructionStepImage
from .models import LiveSession, LiveChatMessage
from users.serializers import UserProfileSerializer
from django.conf import settings
from django.contrib.auth import get_user_model

class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields = ['id']


class IngredientPriceEntrySerializer(serializers.ModelSerializer):
    """Serializer used by verified contributors to manage ingredient prices/weights."""

    price_per_kg = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    default_unit_weight_g = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'default_unit_weight_g', 'price_per_kg']
        read_only_fields = ['id', 'name']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        price_obj = getattr(instance, 'price', None)
        data['price_per_kg'] = str(price_obj.price_per_kg) if price_obj else None
        return data

    def update(self, instance, validated_data):
        price_value = validated_data.pop('price_per_kg', serializers.empty)
        instance = super().update(instance, validated_data)

        if price_value is not serializers.empty:
            if price_value is None:
                IngredientPrice.objects.filter(ingredient=instance).delete()
            else:
                price_obj, _ = IngredientPrice.objects.get_or_create(ingredient=instance)
                price_obj.price_per_kg = price_value
                price_obj.save(update_fields=['price_per_kg', 'updated_at'])

        return instance

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
        
        # Create new ingredient if it doesn't exist (use title-cased name)
        try:
            ingredient = Ingredient.objects.get(name__iexact=clean_name)
        except Ingredient.DoesNotExist:
            ingredient, created = Ingredient.objects.get_or_create(
                name=name.title(),
                defaults={
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
    # Rating fields
    average_rating = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    # Like and comment counts
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    # Accept names instead of IDs for creation
    category_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    cuisine_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    tag_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    # Convert image field to full URL
    image = serializers.SerializerMethodField()
    # Write-only field for image uploads
    image_upload = serializers.ImageField(write_only=True, required=False)
    # Multiple image support
    images = serializers.SerializerMethodField()
    image_uploads = serializers.ListField(child=serializers.ImageField(), write_only=True, required=False)
    # Per-step images: accept list of {step_index, image, caption}
    step_images = serializers.SerializerMethodField()
    step_images_upload = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'id', 'contributor', 'contributor_id', 'title', 'description', 'instructions',
            'prep_time', 'cook_time', 'servings', 'created_at', 'updated_at', 'ingredients',
            'ingredients_data', 'approved', 'feedback', 'slug', 'is_active', 'difficulty', 'source',
            'categories', 'category_names', 'cuisines', 'cuisine_names', 'tags', 'tag_names', 'image', 'image_upload',
            'average_rating', 'rating_count', 'like_count', 'comment_count', 'estimated_cost', 'images', 'image_uploads', 'step_images', 'step_images_upload'
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

    def get_images(self, obj):
        request = self.context.get('request')
        images = []
        for img in getattr(obj, 'images').all():
            url = img.image.url
            if request:
                url = request.build_absolute_uri(url)
            images.append({'id': img.id, 'url': url, 'caption': img.caption, 'order': img.order})
        return images

    def get_step_images(self, obj):
        request = self.context.get('request')
        images = []
        for si in getattr(obj, 'step_images').all():
            url = si.image.url
            if request:
                url = request.build_absolute_uri(url)
            images.append({'id': si.id, 'step_index': si.step_index, 'url': url, 'caption': si.caption})
        return images

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

    def _get_uploaded_files(self, key):
        """Retrieve uploaded files from the request for a given key."""
        request = self.context.get('request') if hasattr(self, 'context') else None
        if request is None:
            return []

        files = []
        candidate_keys = [key, f'{key}[]']

        def _collect_from(source):
            collected = []
            if source is None:
                return collected
            if hasattr(source, 'getlist'):
                for candidate in candidate_keys:
                    for item in source.getlist(candidate):
                        if item and hasattr(item, 'read'):
                            collected.append(item)
            else:
                for candidate in candidate_keys:
                    item = source.get(candidate)
                    if item and hasattr(item, 'read'):
                        collected.append(item)
            return collected

        data = getattr(request, 'data', None)
        files.extend(_collect_from(data))

        request_files = getattr(request, 'FILES', None)
        files.extend(_collect_from(request_files))

        raw_request = getattr(request, '_request', None)
        if raw_request is not None:
            files.extend(_collect_from(getattr(raw_request, 'FILES', None)))
            files.extend(_collect_from(getattr(raw_request, 'POST', None)))

        meta = getattr(request, 'META', None)
        if isinstance(meta, dict):
            meta_files = meta.get('files')
            if isinstance(meta_files, (list, tuple)):
                for name, file_obj in meta_files:
                    if name in candidate_keys and file_obj and hasattr(file_obj, 'read'):
                        files.append(file_obj)

        # Preserve order and remove duplicates while keeping first occurrence
        seen = set()
        ordered = []
        for file_obj in files:
            identifier = id(file_obj)
            if identifier not in seen:
                seen.add(identifier)
                ordered.append(file_obj)

        return ordered

    def _normalize_step_images_payload(self, raw_value):
        """Accept JSON strings or lists and pair with uploaded files appropriately."""
        uploaded_files = self._get_uploaded_files('step_images_upload')

        # QueryDict may provide list containing both string metadata and files; strip files here
        if isinstance(raw_value, list):
            non_file_entries = [entry for entry in raw_value if not hasattr(entry, 'read')]
            if len(non_file_entries) == 1:
                parsed_source = non_file_entries[0]
            elif len(non_file_entries) > 1:
                parsed_source = non_file_entries
            else:
                parsed_source = []
        else:
            parsed_source = raw_value

        parsed = parsed_source
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                parsed = []
        elif parsed is None:
            parsed = []

        if isinstance(parsed, dict):
            parsed = [parsed]
        elif not isinstance(parsed, list):
            parsed = []

        normalized = []
        file_index = 0
        for item in parsed:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except json.JSONDecodeError:
                    item = {'step_index': item}
            elif not isinstance(item, dict):
                item = {'step_index': item}

            image_obj = item.get('image')
            if isinstance(image_obj, str) or image_obj is None:
                image_obj = uploaded_files[file_index] if file_index < len(uploaded_files) else None
                file_index += 1 if image_obj is not None else 0

            normalized.append({
                'step_index': item.get('step_index'),
                'caption': item.get('caption', ''),
                'image': image_obj,
            })

        # Attach any leftover uploaded files that did not map to payload entries
        while file_index < len(uploaded_files):
            normalized.append({
                'step_index': None,
                'caption': '',
                'image': uploaded_files[file_index],
            })
            file_index += 1

        return normalized

    def create(self, validated_data):
        # Extract ingredients and related lists
        ingredients_data = validated_data.pop('ingredients_data', [])
        category_names = validated_data.pop('category_names', [])
        cuisine_names = validated_data.pop('cuisine_names', [])
        tag_names = validated_data.pop('tag_names', [])

    # Extract image uploads lists
        image_uploads = validated_data.pop('image_uploads', None)
        if not image_uploads:
            image_uploads = self._get_uploaded_files('image_uploads')
        else:
            image_uploads = [f for f in image_uploads if f]
        step_images_upload_raw = validated_data.pop('step_images_upload', [])
        step_images_upload = self._normalize_step_images_payload(step_images_upload_raw)

        # Handle single image upload (backwards-compatible)
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

        # Handle multiple recipe image uploads (if any)
        # Enforce max 3 images per recipe
        if len(image_uploads) > 3:
            # delete the created recipe to avoid orphan
            recipe.delete()
            raise serializers.ValidationError({'image_uploads': 'A recipe may include at most 3 images.'})

        for idx, img in enumerate(image_uploads):
            RecipeImage.objects.create(
                recipe=recipe,
                image=img,
                order=idx,
                uploaded_by=(self.context.get('request').user if self.context.get('request') else None)
            )

        # Handle per-step image uploads
        for step_obj in step_images_upload:
            # Expect dict with step_index and image (and optional caption)
            try:
                step_index = int(step_obj.get('step_index'))
                image = step_obj.get('image')
            except Exception:
                continue
            caption = step_obj.get('caption', '')
            if step_index and image:
                InstructionStepImage.objects.update_or_create(
                    recipe=recipe,
                    step_index=step_index,
                    defaults={
                        'image': image,
                        'caption': caption,
                        'uploaded_by': (self.context.get('request').user if self.context.get('request') else None)
                    }
                )

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients_data', None)
        category_names = validated_data.pop('category_names', None)
        cuisine_names = validated_data.pop('cuisine_names', None)
        tag_names = validated_data.pop('tag_names', None)
        image_uploads = validated_data.pop('image_uploads', None)
        if image_uploads:
            image_uploads = [f for f in image_uploads if f]
        else:
            image_uploads = None
        step_images_upload_raw = validated_data.pop('step_images_upload', None)
        if step_images_upload_raw is not None:
            step_images_upload = self._normalize_step_images_payload(step_images_upload_raw)
        else:
            step_images_upload = None

        # Handle single image upload (backwards-compatible)
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

        # Handle new multiple image uploads (append)
        if image_uploads:
            existing_count = instance.images.count()
            for idx, img in enumerate(image_uploads):
                RecipeImage.objects.create(
                    recipe=instance,
                    image=img,
                    order=existing_count + idx,
                    uploaded_by=(self.context.get('request').user if self.context.get('request') else None)
                )

        # Handle per-step image uploads
        if step_images_upload is not None:
            for step_obj in step_images_upload:
                try:
                    step_index = int(step_obj.get('step_index'))
                    image = step_obj.get('image')
                except Exception:
                    continue
                caption = step_obj.get('caption', '')
                if step_index and image:
                    InstructionStepImage.objects.update_or_create(
                        recipe=instance,
                        step_index=step_index,
                        defaults={
                            'image': image,
                            'caption': caption,
                            'uploaded_by': (self.context.get('request').user if self.context.get('request') else None)
                        }
                    )

        return instance

    def validate(self, data):
        """Validate recipe data."""
        ingredients_data = []

        if 'ingredients_data' in data:
            ingredients_data = data['ingredients_data']
        elif hasattr(self, 'initial_data') and 'ingredients' in self.initial_data:
            ingredients_data = self.initial_data['ingredients']

        if len(ingredients_data) < 4:
            raise serializers.ValidationError('A recipe must have at least 4 ingredients.')

        instructions = data.get('instructions', '')
        if not instructions or len(instructions.strip()) < 20:
            raise serializers.ValidationError('Please provide well-explained steps (at least 20 characters).')

        return data


class RecipeRatingSerializer(serializers.ModelSerializer):
    """Serializer for viewing RecipeRating model."""
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = RecipeRating
        fields = ['id', 'user', 'rating', 'review', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class RecipeRatingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating RecipeRating model."""
    
    class Meta:
        model = RecipeRating
        fields = ['recipe', 'rating', 'review']
        
    def validate(self, data):
        """
        Ensure the user can only rate a recipe once (will update if already exists).
        """
        user = self.context['request'].user
        recipe = data.get('recipe')
        
        # Check if this is an update to an existing rating
        if self.instance:
            return data
            
        # Check if user has already rated this recipe
        existing_rating = RecipeRating.objects.filter(user=user, recipe=recipe).first()
        if existing_rating:
            raise serializers.ValidationError("You have already rated this recipe. Please edit your existing rating.")
        
        return data
        
    def create(self, validated_data):
        """Create a new rating."""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

class RecipeLikeSerializer(serializers.ModelSerializer):
    """Serializer for viewing RecipeLike model."""
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = RecipeLike
        fields = ['id', 'user', 'created_at']
        read_only_fields = ['id', 'created_at']


class RecipeLikeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/deleting RecipeLike."""
    
    class Meta:
        model = RecipeLike
        fields = ['recipe']
        
    def validate(self, data):
        """Ensure the user can only like a recipe once."""
        user = self.context['request'].user
        recipe = data.get('recipe')
        
        # Check if this is an update
        if self.instance:
            return data
            
        # Check if user has already liked this recipe
        existing_like = RecipeLike.objects.filter(user=user, recipe=recipe).first()
        if existing_like:
            raise serializers.ValidationError("You have already liked this recipe.")
        
        return data
        
    def create(self, validated_data):
        """Create a new like."""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class RecipeCommentSerializer(serializers.ModelSerializer):
    """Serializer for viewing RecipeComment model."""
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = RecipeComment
        fields = ['id', 'user', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RecipeCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating RecipeComment."""
    
    class Meta:
        model = RecipeComment
        fields = ['recipe', 'content']
        
    def create(self, validated_data):
        """Create a new comment."""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)


class LiveSessionSerializer(serializers.ModelSerializer):
    host = UserProfileSerializer(read_only=True)
    host_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='host', write_only=True, required=False)

    class Meta:
        model = LiveSession
        fields = [
            'id',
            'host',
            'host_id',
            'title',
            'description',
            'slug',
            'is_live',
            'started_at',
            'ended_at',
            'stream_key',
            'viewer_count',
            'provider',
            'external_room_name',
            'external_room_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'stream_key', 'viewer_count', 'provider', 'external_room_name', 'external_room_url', 'created_at', 'updated_at']


class LiveChatMessageSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), source='user', write_only=True, required=False)

    class Meta:
        model = LiveChatMessage
        fields = ['id', 'session', 'user', 'user_id', 'message', 'created_at']
        read_only_fields = ['id', 'created_at', 'user']