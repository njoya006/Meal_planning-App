from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Recipe, Ingredient, Category, Cuisine, Tag
from .serializers import RecipeSerializer, IngredientSerializer, CategorySerializer, CuisineSerializer, TagSerializer
from .permissions import IsVerifiedContributor # Import your custom permission
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.db.models import Count
from .bad_ingredients import get_bad_ingredient_pairs, get_bad_ingredient_triplets, get_bad_ingredient_categories, get_ingredient_substitutions
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RecipeSerializer

    # Permission configuration:
    # - IsAuthenticatedOrReadOnly: Allows unauthenticated users to read (GET), but requires authentication for others.
    # - IsVerifiedContributor: Further restricts write operations to only verified contributors.
    permission_classes = [IsAuthenticatedOrReadOnly, IsVerifiedContributor]

    @method_decorator(cache_page(60 * 5), name='list')  # Cache list endpoint for 5 minutes
    @method_decorator(cache_page(60 * 10), name='retrieve')  # Cache detail endpoint for 10 minutes
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def perform_create(self, serializer):
        # Automatically set the contributor and audit fields to the current authenticated user
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(contributor=user, user=user)

    def perform_update(self, serializer):
        # Update audit fields on update
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    @action(detail=False, methods=['post'], url_path='suggest-by-ingredients')
    def suggest_by_ingredients(self, request):
        ingredient_names = request.data.get('ingredient_names', [])
        if not isinstance(ingredient_names, list) or len(ingredient_names) < 4:
            return Response({'error': 'Please provide at least 4 ingredient names.'}, status=400)
        lower_names = [name.strip().lower() for name in ingredient_names]
        # Use dynamic bad ingredient logic
        bad_pairs = get_bad_ingredient_pairs()
        bad_triplets = get_bad_ingredient_triplets()
        bad_categories = get_bad_ingredient_categories()
        # Check for bad ingredient pairs
        for i in range(len(lower_names)):
            for j in range(i + 1, len(lower_names)):
                pair = tuple(sorted((lower_names[i], lower_names[j])))
                if pair in bad_pairs:
                    return Response({'message': 'i dey sorry, dis app no fit cook chop with this spices.'}, status=200)
        # Check for bad ingredient triplets
        if len(lower_names) >= 3:
            from itertools import combinations
            for triplet in combinations(lower_names, 3):
                if tuple(sorted(triplet)) in bad_triplets:
                    return Response({'message': 'i dey sorry, dis app no fit cook chop with this spices.'}, status=200)
        # Check for bad ingredient categories
        for category, bad_set in bad_categories.items():
            if set(lower_names) & bad_set:
                return Response({'message': f'This app cannot suggest meals with {category} items: {", ".join(set(lower_names) & bad_set)}.'}, status=200)
        # Get ingredient IDs from names
        ingredients = Ingredient.objects.filter(name__in=ingredient_names)
        if ingredients.count() < 4:
            return Response({'error': 'Some ingredient names are invalid or missing.'}, status=400)
        ingredient_ids = list(ingredients.values_list('id', flat=True))
        recipes = Recipe.objects.annotate(
            matched_ingredients=Count(
                'ingredients',
                filter=models.Q(ingredients__in=ingredient_ids),
                distinct=True
            )
        ).filter(matched_ingredients__gte=1)  # Suggest recipes with at least 1 matching ingredient
        suggestions = []
        ingredient_substitutions = get_ingredient_substitutions()
        for recipe in recipes:
            recipe_ingredient_names = set([n.lower() for n in recipe.ingredients.values_list('name', flat=True)])
            user_ingredient_names = set(lower_names)
            missing_ingredients = list(recipe_ingredient_names - user_ingredient_names)
            substitutions = {}
            for missing in missing_ingredients:
                if missing in ingredient_substitutions:
                    substitutions[missing] = ingredient_substitutions[missing]
            if user_ingredient_names.issuperset(recipe_ingredient_names):
                suggestions.append({
                    'recipe': self.get_serializer(recipe).data,
                    'missing_ingredients': [],
                    'message': 'You have all the ingredients for this meal!',
                    'substitutions': {}
                })
            elif len(user_ingredient_names & recipe_ingredient_names) >= 4:
                suggestions.append({
                    'recipe': self.get_serializer(recipe).data,
                    'missing_ingredients': missing_ingredients,
                    'message': f"You are missing the following ingredients to prepare this meal: {', '.join(missing_ingredients)}. Please add or purchase them.",
                    'substitutions': substitutions
                })
        if not suggestions:
            return Response({'message': 'No recipes found that contain all the provided ingredients.'}, status=200)
        # Analytics: Log the query (for demonstration, print to console)
        print(f"[Analytics] User ingredients: {ingredient_names} | Suggestions: {len(suggestions)}")
        return Response({'suggested_recipes': suggestions, 'info': 'Recipes are sorted by best match.'})

    @action(detail=True, methods=['post'], url_path='approve', permission_classes=[IsVerifiedContributor])
    def approve_recipe(self, request, pk=None):
        recipe = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Only admins can approve recipes.'}, status=status.HTTP_403_FORBIDDEN)
        recipe.approved = True
        recipe.feedback = request.data.get('feedback', 'Recipe approved and added to the system.')
        recipe.save()
        return Response({'message': 'Recipe approved.', 'feedback': recipe.feedback})

    @action(detail=True, methods=['post'], url_path='reject', permission_classes=[IsVerifiedContributor])
    def reject_recipe(self, request, pk=None):
        recipe = self.get_object()
        if not request.user.is_staff:
            return Response({'error': 'Only admins can reject recipes.'}, status=status.HTTP_403_FORBIDDEN)
        recipe.approved = False
        recipe.feedback = request.data.get('feedback', 'Recipe was not approved. Please review and resubmit.')
        recipe.save()
        return Response({'message': 'Recipe rejected.', 'feedback': recipe.feedback})

    @action(detail=False, methods=['get'], url_path='all', permission_classes=[IsAuthenticatedOrReadOnly])
    def all_recipes(self, request):
        """Admin-only endpoint to view all recipes, including inactive ones."""
        if not request.user.is_staff:
            return Response({'error': 'Only admins can view all recipes.'}, status=status.HTTP_403_FORBIDDEN)
        queryset = Recipe.objects.all().order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

class CuisineViewSet(viewsets.ModelViewSet):
    queryset = Cuisine.objects.all().order_by('name')
    serializer_class = CuisineSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    def perform_update(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)