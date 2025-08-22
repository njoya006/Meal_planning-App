# planner/views.py

from rest_framework import viewsets, permissions, filters
from .models import MealPlan, NutritionInfo, DietaryRule
from .serializers import MealPlanSerializer, NutritionInfoSerializer, DietaryRuleSerializer
from .permissions import IsVerifiedContributor # Used by NutritionInfoViewSet
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
        user = self.request.user
        preferences = []
        try:
            user_prefs_obj = user.dietary_preferences
            if user_prefs_obj and user_prefs_obj.preferences:
                preferences = [p.strip().lower() for p in user_prefs_obj.preferences.split(',') if p.strip()]
        except Exception:
            preferences = []

        if 'recipe' not in serializer.validated_data:
            raise serializers.ValidationError({'recipe': 'Recipe information is missing or invalid.'})

        recipe_data = serializer.validated_data['recipe']
        try:
            if isinstance(recipe_data, dict):
                recipe_id = recipe_data.get('id')
                if recipe_id:
                    recipe = Recipe.objects.get(id=recipe_id)
                else:
                    recipe_title = recipe_data.get('title')
                    recipe = Recipe.objects.filter(title=recipe_title).first()
                    if not recipe:
                        raise serializers.ValidationError("Recipe not found.")
            else:
                recipe = recipe_data

            if preferences:
                recipe_ingredient_names = set(i.strip().lower() for i in recipe.ingredients.values_list('name', flat=True))
                preferences_set = set(p.strip().lower() for p in preferences)
                print(f"[DEBUG] User dietary preferences: {preferences_set}")
                print(f"[DEBUG] Recipe ingredient names: {recipe_ingredient_names}")
                forbidden_ingredients = recipe_ingredient_names.intersection(preferences_set)
                if forbidden_ingredients:
                    raise serializers.ValidationError(f"This recipe contains ingredients you wish to avoid: {', '.join(forbidden_ingredients)}.")
            serializer.save(user=user)
        except serializers.ValidationError as ve:
            # Let DRF handle these
            raise ve
        except Exception as e:
            import traceback
            print('[ERROR] Exception in perform_create:', traceback.format_exc())
            raise serializers.ValidationError({'detail': 'An unexpected error occurred. Please check your input and try again.'})

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
        # --- USER PROFILE BASIC INGREDIENTS LOGIC ---
        user_profile_basics = []
        if hasattr(request.user, 'basic_ingredients') and request.user.basic_ingredients:
            user_profile_basics = [b.strip().lower() for b in request.user.basic_ingredients.split(',') if b.strip()]
        # Merge all sources of basics
        all_basic_ingredients = list(set(basic_ingredients + user_profile_basics))
        # --- API Flexibility: Allow opt-out of assumed basics via query param ---
        assume_basics = request.query_params.get('assume_basics', 'true').lower() != 'false'
        # Only add basic_ingredients if not opted out
        if assume_basics:
            combined_positive_prefs = list(set(preferences + all_basic_ingredients + user_pantry_ingredients))
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

    @action(detail=False, methods=['get'], url_path='grocery-list', permission_classes=[IsAuthenticatedOrReadOnly])
    def grocery_list(self, request):
        """Aggregate ingredients for a set of meal plans into a polished grocery list.

        Features:
        - Accepts `ids`, or `start`/`end` date range, and optional `servings` scaling.
        - Consolidates identical ingredients; multiplies quantities by recipe occurrence count.
        - Normalizes ingredient names using `IngredientSynonym` where available.
        - Performs simple unit normalization & conversion for common units (g/kg/mg/l/ml/cup/tbsp/tsp/oz/lb).
        - Returns JSON by default, or CSV when `format=csv` is provided.
        - Adds simple shopping categories via keyword heuristics.
        """
        # local imports for clarity and to avoid circular import at module load
        from django.http import HttpResponse
        import csv, io
        from recipes.models import IngredientSynonym, Ingredient

        user = request.user
        if not user or not user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=401)

        ids_param = request.query_params.get('ids')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        scale_target = request.query_params.get('servings')
        resp_format = request.query_params.get('format', 'json').lower()

        try:
            scale_target = int(scale_target) if scale_target is not None else None
        except (TypeError, ValueError):
            return Response({'error': 'Invalid servings parameter; must be integer.'}, status=400)

        # Select meal plans
        if ids_param:
            try:
                ids = [int(x) for x in ids_param.split(',') if x.strip()]
                mealplans = MealPlan.objects.filter(user=user, id__in=ids).select_related('recipe')
            except ValueError:
                return Response({'error': 'Invalid ids parameter.'}, status=400)
        else:
            qs = MealPlan.objects.filter(user=user)
            if start:
                qs = qs.filter(date__gte=start)
            if end:
                qs = qs.filter(date__lte=end)
            mealplans = qs.select_related('recipe')

        if not mealplans.exists():
            return Response({'grocery_list': [], 'per_recipe': {}, 'meta': {'message': 'No meal plans found for given criteria.'}}, status=200)

        # Build recipe occurrence counts (if same recipe appears multiple times, count occurrences)
        recipe_counts = {}
        for mp in mealplans:
            rid = mp.recipe.id if mp.recipe else None
            if rid is None:
                continue
            recipe_counts[rid] = recipe_counts.get(rid, 0) + 1

        # Load synonym map: synonym_lower -> canonical_name
        synonyms = {}
        for syn in IngredientSynonym.objects.select_related('ingredient').all():
            try:
                synonyms[syn.name.strip().lower()] = syn.ingredient.name.strip()
            except Exception:
                continue

        # Unit groups & conversion to base units
        weight_units = {'g', 'kg', 'mg', 'lb', 'oz'}
        volume_units = {'ml', 'l', 'cup', 'tbsp', 'tsp'}
        count_units = {'piece', 'slice', 'clove', 'cloves', 'bunch', 'can', 'package', 'bottle', 'handful', 'pinch', 'dash'}

        # conversion factors to base unit (g for weight, ml for volume)
        to_grams = {'g':1.0, 'kg':1000.0, 'mg':0.001, 'lb':453.592, 'oz':28.3495}
        to_ml = {'ml':1.0, 'l':1000.0, 'cup':240.0, 'tbsp':15.0, 'tsp':5.0}

        def canonical_name(name):
            if not name:
                return name
            key = name.strip().lower()
            return synonyms.get(key, name.strip())

        def categorize_name(name):
            n = name.lower()
            produce = ['tomato','tomatoes','onion','onions','garlic','ginger','lettuce','spinach','carrot','pepper','pepperoni','cucumber']
            dairy = ['milk','cheese','butter','yogurt','cream']
            protein = ['chicken','beef','pork','fish','egg','eggs','tofu','lentil','beans']
            pantry = ['rice','flour','sugar','salt','oil','vinegar','soy sauce','water','tomato paste','tomatoes']
            bakery = ['bread']
            if any(p in n for p in produce):
                return 'Produce'
            if any(d in n for d in dairy):
                return 'Dairy'
            if any(p in n for p in protein):
                return 'Protein'
            if any(p in n for p in pantry):
                return 'Pantry'
            if any(b in n for b in bakery):
                return 'Bakery'
            return 'Other'

        # Aggregation: key = (canonical_name_lower, unit_type, base_unit_or_unit_str)
        aggregated = {}
        per_recipe = {}

        for mp in mealplans:
            recipe = mp.recipe
            if not recipe:
                continue
            per_recipe.setdefault(recipe.id, {'title': recipe.title, 'ingredients': []})

            occurrences = recipe_counts.get(recipe.id, 1)

            # Determine scaling factor for servings
            factor = 1.0
            if scale_target and recipe.servings:
                try:
                    factor = float(scale_target) / float(recipe.servings)
                except Exception:
                    factor = 1.0

            # Multiply by occurrences
            total_multiplier = factor * occurrences

            for ri in recipe.recipeingredient_set.select_related('ingredient').all():
                ing = ri.ingredient
                if not ing:
                    continue
                raw_name = ing.name
                name = canonical_name(raw_name)
                unit = (ri.unit or '').strip().lower()
                qty = ri.quantity if ri.quantity is not None else 0
                qty_scaled = float(qty) * total_multiplier

                # Normalize units when possible
                key_unit = unit
                normalized_qty = qty_scaled
                if unit in weight_units:
                    # convert to grams
                    factor_conv = to_grams.get(unit, None)
                    if factor_conv:
                        normalized_qty = qty_scaled * factor_conv
                        key_unit = 'g'
                elif unit in volume_units:
                    factor_conv = to_ml.get(unit, None)
                    if factor_conv:
                        normalized_qty = qty_scaled * factor_conv
                        key_unit = 'ml'
                else:
                    # keep as-is (pieces etc.)
                    key_unit = unit or 'unit'

                key = (name.strip().lower(), key_unit)
                if key not in aggregated:
                    aggregated[key] = {
                        'name': name.strip(),
                        'unit': key_unit,
                        'quantity': normalized_qty,
                        'recipes': set([recipe.id])
                    }
                else:
                    try:
                        aggregated[key]['quantity'] += normalized_qty
                    except Exception:
                        pass
                    aggregated[key]['recipes'].add(recipe.id)

                per_recipe[recipe.id]['ingredients'].append({
                    'name': name.strip(),
                    'unit': key_unit,
                    'quantity': round(normalized_qty, 3)
                })

        # Prepare final grocery list with pretty units (convert base units back to human-friendly where appropriate)
        grocery_list = []
        for (name_key, unit_key), v in aggregated.items():
            qty = v['quantity']
            display_unit = unit_key
            display_qty = qty
            # If grams and large, show kg
            if unit_key == 'g' and qty >= 1000:
                display_qty = round(qty / 1000.0, 3)
                display_unit = 'kg'
            elif unit_key == 'ml' and qty >= 1000:
                display_qty = round(qty / 1000.0, 3)
                display_unit = 'l'
            else:
                display_qty = round(qty, 3)

            grocery_list.append({
                'name': v['name'],
                'unit': display_unit,
                'quantity': display_qty,
                'raw_quantity': round(v['quantity'], 3),
                'recipes': sorted(list(v['recipes'])),
                'category': categorize_name(v['name'])
            })

        # Sort grocery list by category then name
        grocery_list.sort(key=lambda x: (x['category'], x['name'].lower()))

        meta = {
            'mealplan_count': mealplans.count(),
            'scaled_to_servings': scale_target,
            'generated_for_user': user.username,
        }

        # If CSV requested, stream a CSV file
        if resp_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Ingredient', 'Quantity', 'Unit', 'Category', 'Recipes'])
            for item in grocery_list:
                writer.writerow([item['name'], item['quantity'], item['unit'], item['category'], ' '.join(str(r) for r in item['recipes'])])
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            filename = f"grocery_list_{user.username}.csv"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        # JSON response
        return Response({
            'grocery_list': grocery_list,
            'per_recipe': per_recipe,
            'meta': meta
        }, status=200)

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
