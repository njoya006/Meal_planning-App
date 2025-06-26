from difflib import get_close_matches

from django.db import models
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .bad_ingredients import (
    get_bad_ingredient_pairs, 
    get_bad_ingredient_triplets, 
    get_bad_ingredient_categories, 
    get_ingredient_substitutions
)
from .models import Recipe, Ingredient, Category, Cuisine, Tag
from .permissions import IsVerifiedContributor
from .serializers import (
    RecipeSerializer, 
    IngredientSerializer, 
    CategorySerializer, 
    CuisineSerializer, 
    TagSerializer
)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RecipeSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file uploads

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
        serializer.save(contributor=user)

    def perform_update(self, serializer):
        # Update audit fields on update
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(contributor=user)

    @action(detail=False, methods=['post'], url_path='suggest-by-ingredients')
    def suggest_by_ingredients(self, request):
        ingredient_names = request.data.get('ingredient_names', [])
        if not isinstance(ingredient_names, list) or len(ingredient_names) < 4:
            return Response({'error': 'Please provide at least 4 ingredient names.'}, status=400)
        # Normalize input
        lower_names = [name.strip().lower() for name in ingredient_names]
        # Get all valid ingredient names from DB
        all_ingredients = list(Ingredient.objects.values_list('name', flat=True))
        all_ingredients_lower = [n.lower() for n in all_ingredients]
        valid_names = []
        suggestions = {}
        for name in lower_names:
            if name in all_ingredients_lower:
                valid_names.append(all_ingredients[all_ingredients_lower.index(name)])
            else:
                # Fuzzy match: suggest closest ingredient(s)
                matches = get_close_matches(name, all_ingredients_lower, n=1, cutoff=0.7)
                if matches:
                    suggestions[name] = all_ingredients[all_ingredients_lower.index(matches[0])]
                else:
                    suggestions[name] = []
        # Accept fuzzy matches if at least 4 are valid or can be auto-corrected
        final_names = valid_names + [v for k, v in suggestions.items() if v]
        if len(final_names) < 4:
            return Response({
                'error': 'Some ingredient names are invalid or missing.',
                'valid_ingredients': valid_names,
                'suggestions': suggestions
            }, status=400)
        # Use final_names for the rest of the logic
        lower_names = [n.lower() for n in final_names]
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
        ingredients = Ingredient.objects.filter(name__in=final_names)
        ingredient_ids = list(ingredients.values_list('id', flat=True))
        recipes = Recipe.objects.annotate(
            matched_ingredients=Count(
                'ingredients',
                filter=models.Q(ingredients__in=ingredient_ids),
                distinct=True
            )
        ).filter(matched_ingredients__gte=1)  # Suggest recipes with at least 1 matching ingredient
        suggestions_list = []
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
                suggestions_list.append({
                    'recipe': self.get_serializer(recipe).data,
                    'missing_ingredients': [],
                    'message': 'You have all the ingredients for this meal!',
                    'substitutions': {}
                })
            elif len(user_ingredient_names & recipe_ingredient_names) >= 4:
                suggestions_list.append({
                    'recipe': self.get_serializer(recipe).data,
                    'missing_ingredients': missing_ingredients,
                    'message': f"You are missing the following ingredients to prepare this meal: {', '.join(missing_ingredients)}. Please add or purchase them.",
                    'substitutions': substitutions
                })
        if not suggestions_list:
            return Response({'message': 'No recipes found that contain all the provided ingredients.'}, status=200)
        # Analytics: Log the query (for demonstration, print to console)
        print(f"[Analytics] User ingredients: {ingredient_names} | Suggestions: {len(suggestions_list)}")
        return Response({'suggested_recipes': suggestions_list, 'info': 'Recipes are sorted by best match.'})

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

class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ingredient search and discovery."""
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @method_decorator(cache_page(60 * 10), name='list')  # Cache for 10 minutes
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """Search ingredients by name with autocomplete functionality."""
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({'error': 'Query parameter "q" is required.'}, status=400)
        
        if len(query) < 2:
            return Response({'error': 'Query must be at least 2 characters long.'}, status=400)
        
        # Search for ingredients that contain the query (case-insensitive)
        ingredients = Ingredient.objects.filter(
            name__icontains=query
        ).order_by('name')[:20]  # Limit to 20 results
        
        serializer = self.get_serializer(ingredients, many=True)
        
        return Response({
            'ingredients': serializer.data,
            'count': ingredients.count(),
            'query': query
        })
    
    @action(detail=False, methods=['get'], url_path='suggestions')
    def suggestions(self, request):
        """Get ingredient suggestions based on partial input."""
        query = request.query_params.get('q', '').strip().lower()
        
        if not query:
            return Response({'error': 'Query parameter "q" is required.'}, status=400)
        
        # Get ingredients that start with the query
        starts_with = Ingredient.objects.filter(
            name__istartswith=query
        ).order_by('name')[:10]
        
        # Get ingredients that contain the query but don't start with it
        contains = Ingredient.objects.filter(
            name__icontains=query
        ).exclude(
            name__istartswith=query
        ).order_by('name')[:10]
        
        # Combine results, prioritizing "starts with" matches
        suggestions = list(starts_with) + list(contains)
        
        serializer = self.get_serializer(suggestions, many=True)
        
        return Response({
            'suggestions': serializer.data,
            'count': len(suggestions),
            'query': query
        })
    
    @action(detail=False, methods=['get'], url_path='popular')
    def popular(self, request):
        """Get most commonly used ingredients."""
        # Get ingredients ordered by how many recipes use them
        popular_ingredients = Ingredient.objects.annotate(
            recipe_count=Count('recipes_used_in')
        ).filter(
            recipe_count__gt=0
        ).order_by('-recipe_count')[:30]
        
        serializer = self.get_serializer(popular_ingredients, many=True)
        
        return Response({
            'popular_ingredients': serializer.data,
            'count': popular_ingredients.count()
        })
    
    @action(detail=False, methods=['get'], url_path='basic')
    def basic_ingredients(self, request):
        """Get basic ingredients that users commonly have."""
        from .models import BasicIngredient
        
        region = request.query_params.get('region', 'global')
        
        # Get basic ingredients for the specified region
        basic_ingredients = BasicIngredient.objects.filter(
            region=region
        ).order_by('name')
        
        return Response({
            'basic_ingredients': [{'name': bi.name} for bi in basic_ingredients],
            'region': region,
            'count': basic_ingredients.count()
        })

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