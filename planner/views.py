# planner/views.py

from rest_framework import viewsets, permissions, filters
from .models import MealPlan, NutritionInfo, DietaryRule
from .serializers import MealPlanSerializer, NutritionInfoSerializer, DietaryRuleSerializer
from .permissions import IsVerifiedContributor
from rest_framework import serializers
from users.models import DietaryPreference
from recipes.models import Recipe, BasicIngredient, UserPantry
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.conf import settings
from recipes.basic_ingredients import DEFAULT_BASIC_INGREDIENTS

class MealPlanViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'recipe__title', 'meal_type']
    ordering_fields = ['date', 'meal_type', 'created_at']

    def get_queryset(self):
        user = self.request.user
        # Filter meal plans for the current user
        queryset = MealPlan.objects.filter(user=user).order_by('date')
        # Optionally filter by dietary preferences if requested
        dietary = self.request.query_params.get('dietary', None)
        if dietary == '1':
            try:
                preferences = user.dietary_preferences.preferences.split(',')
                preferences = [p.strip().lower() for p in preferences if p.strip()]
                if preferences:
                    # Only include meal plans where the recipe matches dietary preferences
                    queryset = queryset.filter(
                        recipe__ingredients__name__in=preferences
                    ).distinct()
            except Exception:
                pass
        return queryset

    def perform_create(self, serializer):
        # Only allow meal plans that match user's dietary preferences
        user = self.request.user
        try:
            preferences = user.dietary_preferences.preferences.split(',')
            preferences = [p.strip().lower() for p in preferences if p.strip()]
        except Exception:
            preferences = []
        recipe = serializer.validated_data['recipe']
        if preferences:
            recipe_ingredient_names = set(recipe.ingredients.values_list('name', flat=True))
            if not recipe_ingredient_names.intersection(preferences):
                raise serializers.ValidationError("This recipe does not match your dietary preferences.")
        serializer.save(user=user)

    @action(detail=False, methods=['get'], url_path='system-recommendations')
    def system_recommendations(self, request):
        """
        Recommend recipes for the current user based on their dietary preferences, pantry, region, and custom rules.
        Supports allergies, exclusions, positive preferences, custom rules, and assumed basic ingredients.
        Use ?assume_basics=false to opt out of assumed basics.
        Returns transparent info and warnings for frontend display.
        """
        user = request.user
        meal_type = request.query_params.get('meal_type', None)
        rule_id = request.query_params.get('rule_id', None)
        # --- BASIC INGREDIENTS LOGIC WITH LOCALIZATION ---
        # Try to get region from user profile, else use 'global'
        user_region = 'global'
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'region'):
            user_region = request.user.profile.region or 'global'
        # Get region-specific basics, fallback to global, then to settings/default
        db_basics = list(BasicIngredient.objects.filter(region=user_region).values_list('name', flat=True))
        if not db_basics and user_region != 'global':
            db_basics = list(BasicIngredient.objects.filter(region='global').values_list('name', flat=True))
        if db_basics:
            basic_ingredients = [b.strip().lower() for b in db_basics]
        else:
            from django.conf import settings
            from recipes.basic_ingredients import DEFAULT_BASIC_INGREDIENTS
            basic_ingredients = [b.strip().lower() for b in getattr(settings, 'BASIC_INGREDIENTS', DEFAULT_BASIC_INGREDIENTS)]
        # --- USER PANTRY LOGIC ---
        user_pantry_ingredients = []
        if request.user.is_authenticated:
            try:
                pantry = UserPantry.objects.get(user=request.user)
                user_pantry_ingredients = list(pantry.ingredients.values_list('name', flat=True))
                user_pantry_ingredients = [i.strip().lower() for i in user_pantry_ingredients]
            except UserPantry.DoesNotExist:
                pass
        try:
            preferences = user.dietary_preferences.preferences.split(',')
            preferences = [p.strip().lower() for p in preferences if p.strip()]
        except Exception:
            preferences = []
        # --- API Flexibility: Allow opt-out of assumed basics via query param ---
        assume_basics = request.query_params.get('assume_basics', 'true').lower() != 'false'
        # Only add basic_ingredients if not opted out
        if assume_basics:
            combined_positive_prefs = list(set(preferences + basic_ingredients + user_pantry_ingredients))
        else:
            combined_positive_prefs = list(set(preferences + user_pantry_ingredients))
        if not preferences and not rule_id:
            return Response({'message': 'No dietary preferences or custom rule set for this user.'}, status=200)
        # Classify preferences
        positive_prefs = []
        exclusion_prefs = []
        allergy_prefs = []
        for pref in preferences:
            if 'allergy' in pref:
                allergy_prefs.append(pref.replace('-allergy', '').replace('allergy', '').strip())
            elif 'exclude' in pref:
                exclusion_prefs.append(pref.replace('exclude-', '').replace('exclude_', '').strip())
            else:
                positive_prefs.append(pref)
        # --- Use combined_positive_prefs for recipe filtering ---
        matching_recipes = Recipe.objects.all()
        if rule_id:
            from .models import DietaryRule
            try:
                rule = DietaryRule.objects.get(id=rule_id)
                if rule.include_ingredients:
                    matching_recipes = matching_recipes.filter(ingredients__name__in=rule.include_ingredients)
                if rule.exclude_ingredients:
                    matching_recipes = matching_recipes.exclude(ingredients__name__in=rule.exclude_ingredients)
            except DietaryRule.DoesNotExist:
                return Response({'message': 'Custom rule not found.'}, status=400)
        # Use the combined list for positive filtering
        if combined_positive_prefs:
            matching_recipes = matching_recipes.filter(ingredients__name__in=combined_positive_prefs)
        if meal_type:
            matching_recipes = matching_recipes.filter(meal_plans__meal_type=meal_type)
        matching_recipes = matching_recipes.distinct()
        exclusion_set = set(exclusion_prefs + allergy_prefs)
        if exclusion_set:
            matching_recipes = matching_recipes.exclude(ingredients__name__in=exclusion_set)
        if rule_id:
            rule = DietaryRule.objects.get(id=rule_id)
            filtered = []
            for recipe in matching_recipes:
                recipe_ingredient_names = set(recipe.ingredients.values_list('name', flat=True))
                match_count = len(recipe_ingredient_names.intersection(set(rule.include_ingredients or [])))
                if rule.min_ingredients and match_count < rule.min_ingredients:
                    continue
                if rule.max_ingredients and rule.max_ingredients > 0 and match_count > rule.max_ingredients:
                    continue
                filtered.append(recipe)
            matching_recipes = filtered
        # Rank by number of user preferences matched (excluding basics for ranking)
        recipe_scores = []
        for recipe in matching_recipes:
            recipe_ingredient_names = set(recipe.ingredients.values_list('name', flat=True))
            # Only count user preferences for ranking, not basics
            user_only_prefs = set(preferences)
            score = len(recipe_ingredient_names.intersection(user_only_prefs))
            recipe_scores.append((score, recipe))
        recipe_scores.sort(reverse=True)
        top_recipes = [r for s, r in recipe_scores[:10]]
        from recipes.serializers import RecipeSerializer
        data = RecipeSerializer(top_recipes, many=True, context={'request': request}).data
        # --- Transparency: Show assumed basics and pantry in response ---
        response_info = {
            'assumed_basic_ingredients': basic_ingredients,
            'user_pantry_ingredients': user_pantry_ingredients,
            'user_preferences': preferences,
        }
        response_info['assume_basics'] = assume_basics
        # --- Ingredient Availability Warnings ---
        # For each recommended recipe, check if it requires only assumed basics (not in user prefs or pantry)
        warnings = []
        for recipe in top_recipes:
            recipe_ingredient_names = set(recipe.ingredients.values_list('name', flat=True))
            # Ingredients not in user preferences or pantry
            missing = recipe_ingredient_names - set(preferences) - set(user_pantry_ingredients)
            # Only warn if all missing are in basic_ingredients
            missing_basics = [i for i in missing if i in basic_ingredients]
            if missing_basics and set(missing_basics) == missing:
                warnings.append({
                    'recipe_id': recipe.id,
                    'recipe_title': recipe.title,
                    'assumed_basics': missing_basics,
                    'message': f"This recipe assumes you have: {', '.join(missing_basics)}."
                })
        # --- Analytics: Log assumed basic ingredient usage ---
        from recipes.models import BasicIngredientUsage
        for warning in warnings:
            for ingr in warning['assumed_basics']:
                BasicIngredientUsage.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    ingredient=ingr,
                    region=user_region
                )
        return Response({'recommendations': data, 'info': 'Top recipes matching your dietary preferences, basic ingredients, and custom rules.', 'assumptions': response_info, 'warnings': warnings})

class NutritionInfoViewSet(viewsets.ModelViewSet):
    queryset = NutritionInfo.objects.all()
    serializer_class = NutritionInfoSerializer
    permission_classes = [IsVerifiedContributor, IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['recipe__title']
    ordering_fields = ['calories', 'protein', 'fat', 'carbs', 'created_at']

    def perform_create(self, serializer):
        # Ensure nutrition is only added once per recipe
        if NutritionInfo.objects.filter(recipe=serializer.validated_data['recipe']).exists():
            raise serializers.ValidationError("Nutrition info for this recipe already exists.")
        serializer.save()

class DietaryRuleViewSet(viewsets.ModelViewSet):
    queryset = DietaryRule.objects.all()
    serializer_class = DietaryRuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'user__username']
    ordering_fields = ['priority', 'name', 'created_at']

