import logging
from datetime import timedelta
from typing import Optional

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny

# --- Recipe Reviews Endpoint ---
class RecipeReviewPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20

class SearchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

class RecipeReviewsView(APIView):
    def get_permissions(self):
        # Allow any for GET, require auth for POST
        if self.request.method == 'POST':
            from rest_framework.permissions import IsAuthenticated
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, pk):
        """Return paginated reviews (ratings with review text) for a recipe."""
        from .models import RecipeRating
        from .serializers import RecipeRatingSerializer
        reviews = RecipeRating.objects.filter(recipe_id=pk).exclude(review__isnull=True).exclude(review__exact="").order_by('-created_at')
        paginator = RecipeReviewPagination()
        page = paginator.paginate_queryset(reviews, request)
        serializer = RecipeRatingSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, pk):
        """Allow authenticated users to submit a review for a recipe."""
        from .models import RecipeRating, Recipe
        from .serializers import RecipeRatingCreateSerializer
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Recipe not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        data['recipe'] = recipe.id
        serializer = RecipeRatingCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            rating = serializer.save()
            return Response(RecipeRatingSerializer(rating).data, status=201)
        return Response(serializer.errors, status=400)
from difflib import get_close_matches

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models
from django.db.models import Count, Avg, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from rest_framework import status, viewsets, generics, mixins, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from .bad_ingredients import (
    get_bad_ingredient_pairs, 
    get_bad_ingredient_triplets, 
    get_bad_ingredient_categories, 
    get_ingredient_substitutions
)
from .models import Recipe, Ingredient, Category, Cuisine, Tag, RecipeRating, RecipeLike, RecipeComment, LiveSession, LiveChatMessage, IngredientPrice
from .permissions import IsVerifiedContributor, IsLiveSessionHost, IsVerifiedContributorOrStaff
from .serializers import (
    RecipeSerializer, 
    IngredientSerializer, 
    CategorySerializer, 
    CuisineSerializer, 
    TagSerializer,
    RecipeRatingSerializer,
    RecipeRatingCreateSerializer,
    RecipeLikeSerializer,
    RecipeLikeCreateSerializer,
    RecipeCommentSerializer,
    RecipeCommentCreateSerializer,
    LiveSessionSerializer,
    LiveChatMessageSerializer,
    IngredientPriceEntrySerializer
)
from .models import WebsocketToken
from .integrations.daily import DailyClient, DailyAPIError
import datetime, jwt, secrets
from rest_framework.permissions import IsAuthenticated


logger = logging.getLogger(__name__)
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from decimal import Decimal
from django.shortcuts import get_object_or_404

# Fallback price map (per kg) used when IngredientPrice is missing
PRICE_MAP = {
    'rice': Decimal('800'),
    'plantain': Decimal('400'),
    'cassava': Decimal('300'),
    'beans': Decimal('600'),
    'beef': Decimal('1200'),
    'chicken': Decimal('900'),
    'fish': Decimal('900'),
    'palm oil': Decimal('1000'),
    'groundnuts': Decimal('700'),
}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ws_token_view(request):
    """Issue a short-lived, single-use websocket token for the requesting user.

    Response: {"ws_token": "<signed>", "expires_in": 60}
    """
    user = request.user
    ttl = 60  # seconds
    jti = secrets.token_urlsafe(32)
    expires_at = timezone.now() + datetime.timedelta(seconds=ttl)
    # Persist ephemeral token
    WebsocketToken.objects.create(jti=jti, user=user, expires_at=expires_at)
    payload = {
        'jti': jti,
        'user_id': user.id,
        'exp': int((timezone.now() + datetime.timedelta(seconds=ttl)).timestamp()),
    }
    token = jwt.encode(payload, getattr(__import__('django.conf').conf.settings, 'SECRET_KEY'), algorithm='HS256')
    return Response({'ws_token': token, 'expires_in': ttl}, status=status.HTTP_200_OK)


class StreamingProvisioningError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'Unable to provision streaming provider.'
    default_code = 'stream_provision_failed'


class RecipeViewSet(viewsets.ModelViewSet):
    # Provide a default queryset and serializer so DRF can serve list/retrieve endpoints
    queryset = Recipe.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = RecipeSerializer
    # Allow multipart form uploads (images) in create/update
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'pk'
    lookup_value_regex = r'\d+'  # Keep detail routes numeric so /ingredient-prices/ hits the correct viewset

    def get_permissions(self):
        # Allow anyone to read. Require verified contributor for unsafe methods.
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.AllowAny()]
        return [IsVerifiedContributor()]

    def perform_create(self, serializer):
        user = self.request.user if getattr(self.request, 'user', None) and self.request.user.is_authenticated else None
        serializer.save(contributor=user)

    @action(detail=True, methods=['get'], url_path='grocery-list', permission_classes=[IsAuthenticated])
    def grocery_list(self, request, pk=None):
        """Return a grocery list for this recipe with per-ingredient cost estimates and total."""
        recipe = self.get_object()
        items = []
        total = Decimal('0')
        for ri in recipe.recipeingredient_set.select_related('ingredient').all():
            ing = ri.ingredient
            qty = Decimal(str(ri.quantity))
            unit = (ri.unit or '').lower()

            # Determine quantity in kg when possible
            qty_kg = None
            if unit == 'kg':
                qty_kg = qty
            elif unit == 'g':
                qty_kg = qty / Decimal('1000')
            else:
                # Unknown unit: skip cost calculation (could be 'piece', 'cup', etc.)
                qty_kg = None

            # Determine price_per_kg
            price_per_kg = None
            try:
                price_obj = getattr(ing, 'price', None)
                if price_obj and getattr(price_obj, 'price_per_kg', None) is not None:
                    price_per_kg = Decimal(str(price_obj.price_per_kg))
                else:
                    # fallback lookup by name keywords
                    name = ing.name.lower()
                    for key, p in PRICE_MAP.items():
                        if key in name:
                            price_per_kg = p
                            break
            except Exception:
                price_per_kg = None

            cost = None
            if qty_kg is not None and price_per_kg is not None:
                cost = (qty_kg * price_per_kg).quantize(Decimal('0.01'))
                total += cost

            items.append({
                'ingredient_id': ing.id,
                'ingredient_name': ing.name,
                'quantity': float(ri.quantity),
                'unit': ri.unit,
                'unit_price_per_kg': float(price_per_kg) if price_per_kg is not None else None,
                'cost_estimate': float(cost) if cost is not None else None
            })

        return Response({'recipe_id': recipe.id, 'items': items, 'total_estimate': float(total)})


class LiveSessionViewSet(viewsets.ModelViewSet):
    """API for creating and controlling live cooking sessions.

    Note: This only manages metadata and permissions. Use a media server (RTMP/WebRTC)
    for actual video streaming and Django Channels or a websocket service for chat.
    """
    queryset = LiveSession.objects.all().order_by('-created_at')
    serializer_class = LiveSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    # Use slug in URLs so clients can address sessions by human-friendly identifier
    lookup_field = 'slug'

    def get_permissions(self):
        # Anyone can list/view; only verified contributors can start/stop sessions
        if self.action in ['create', 'start', 'stop']:
            return [IsLiveSessionHost()]
        return super().get_permissions()

    def get_queryset(self):
        """Allow clients to request ?status=live even if backend uses different flags.

        The frontend historically asked for `status=live`. Rather than forcing the
        client to change, accept that value and translate it into a queryset that
        matches any session that appears live by our internal representations:
        - `is_live` True
        - `started_at` not null and `ended_at` is null
        - has provider Daily metadata (external_room_name or external_room_url)
        - in_progress flags (legacy) if present
        """
        qs = super().get_queryset()
        status_param = (self.request.query_params.get('status') or '').strip().lower()
        if status_param in {'live', 'started', 'active', 'in_progress'}:
            from django.db.models import Q
            live_q = Q(is_live=True) | Q(started_at__isnull=False, ended_at__isnull=True) | Q(external_room_name__gt='') | Q(external_room_url__gt='')
            if hasattr(LiveSession, 'in_progress'):
                live_q = live_q | Q(in_progress=True)
            qs = qs.filter(live_q)
        return qs

    def perform_create(self, serializer):
        """Ensure the host is set and always provision a Daily room if provider is not set or is local."""
        user = self.request.user if getattr(self.request, 'user', None) and self.request.user.is_authenticated else None
        session = serializer.save(host=user) if user is not None else serializer.save()
        # Always provision a Daily room unless already set
        if not session.provider or session.provider == getattr(session, 'PROVIDER_LOCAL', 'local'):
            session.provider = getattr(session, 'PROVIDER_DAILY', 'daily')
            try:
                self._provision_external_room(session)
            except StreamingProvisioningError:
                session.delete()
                raise
        # If already provisioned, do nothing

    def _provision_external_room(self, session: LiveSession) -> None:
        client = DailyClient.from_settings()
        if not client.is_configured():
            logger.debug("Daily client not configured; skipping room provisioning.")
            return

        if session.provider == LiveSession.PROVIDER_DAILY and session.external_room_name:
            logger.debug("Live session %s already has a Daily room provisioned.", session.pk)
            return

        room_name = self._build_room_name(session)
        try:
            room_response = client.create_room(name=room_name, properties=self._build_room_properties())
        except DailyAPIError as exc:
            logger.warning("Daily room provisioning failed for session %s: %s", session.pk, exc)
            raise StreamingProvisioningError(detail=str(exc))

        session.provider = LiveSession.PROVIDER_DAILY
        session.external_room_name = room_response.get('name', room_name)
        session.external_room_url = room_response.get('url', '')
        session.external_room_data = room_response
        session.save(update_fields=['provider', 'external_room_name', 'external_room_url', 'external_room_data'])

    def _build_room_name(self, session: LiveSession) -> str:
        slug_value = session.slug or f'session-{session.pk or secrets.token_hex(4)}'
        base = slug_value.replace('_', '-').lower()
        candidate = f"{base}-{session.pk}" if session.pk and str(session.pk) not in base else base
        return candidate[:120]

    def _build_room_properties(self) -> dict:
        expires_at = timezone.now() + timedelta(hours=6)
        return {
            'enable_chat': True,
            'enable_screenshare': True,
            'eject_at_room_exp': True,
            'exp': int(expires_at.timestamp()),
        }

    def _mint_streaming_token(self, session: LiveSession, request) -> Optional[dict]:
        client = DailyClient.from_settings()
        if not (client.is_configured() and session.provider == LiveSession.PROVIDER_DAILY and session.external_room_name):
            return None

        user = getattr(request, 'user', None)
        user_id = None
        user_name = 'viewer'
        if user is not None:
            if getattr(user, 'is_authenticated', False):
                user_id = str(getattr(user, 'pk', '')) or None
            user_name = (getattr(user, 'get_full_name', lambda: '')() or getattr(user, 'get_username', lambda: 'viewer')()).strip() or 'viewer'

        is_owner = user is not None and getattr(user, 'is_authenticated', False) and session.host_id == getattr(user, 'id', None)
        expires_at = timezone.now() + timedelta(hours=1)
        try:
            token_payload = client.create_token(
                room_name=session.external_room_name,
                is_owner=is_owner,
                user_name=user_name,
                user_id=user_id,
                exp=int(expires_at.timestamp()),
            )
        except DailyAPIError as exc:
            logger.warning("Daily token creation failed for session %s: %s", session.pk, exc)
            raise StreamingProvisioningError(detail=str(exc))

        token = token_payload.get('token')
        if not token:
            logger.warning("Daily token response missing token for session %s: %s", session.pk, token_payload)
            raise StreamingProvisioningError(detail='Streaming provider returned an invalid token response.')

        if is_owner and not session.is_live:
            # Mark the session live when the host receives a control token so the
            # UI immediately reflects the live state.
            session.is_live = True
            if not session.started_at:
                session.started_at = timezone.now()
            session.ended_at = None
            session.save(update_fields=['is_live', 'started_at', 'ended_at'])

        payload = {
            'token': token,
            'room_name': session.external_room_name,
            'provider': session.provider,
            'expires_at': int(expires_at.timestamp()),
        }
        if session.external_room_url:
            payload['room_url'] = session.external_room_url
        if is_owner:
            payload['is_owner'] = True

        return payload

    @action(detail=True, methods=['post'])
    def start(self, request, slug=None, *args, **kwargs):
        session = self.get_object()
        if session.host != request.user:
            return Response({'error': 'Only the host can start the session.'}, status=status.HTTP_403_FORBIDDEN)
        if session.is_live:
            return Response({'detail': 'Session already live.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            self._provision_external_room(session)
        except StreamingProvisioningError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        session.is_live = True
        session.started_at = timezone.now()
        session.ended_at = None
        session.viewer_count = 0
        session.save(update_fields=['is_live', 'started_at', 'ended_at', 'viewer_count'])
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=['post'])
    def stop(self, request, slug=None, *args, **kwargs):
        session = self.get_object()
        if session.host != request.user:
            return Response({'error': 'Only the host can stop the session.'}, status=status.HTTP_403_FORBIDDEN)
        if not session.is_live:
            return Response({'detail': 'Session is not live.'}, status=status.HTTP_400_BAD_REQUEST)
        from django.utils import timezone
        session.is_live = False
        session.ended_at = timezone.now()
        session.save()
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=['post'])
    def join(self, request, slug=None, *args, **kwargs):
        # In a real implementation, joining returns an access token or websocket URL
        session = self.get_object()
        # Increment viewer count — in practice this should be handled by realtime layer
        session.viewer_count = models.F('viewer_count') + 1
        session.save()
        session.refresh_from_db()
        payload = {
            'detail': 'Joined',
            'viewer_count': session.viewer_count,
            'stream_key': session.stream_key,
            'provider': session.provider,
        }
        if session.provider == LiveSession.PROVIDER_DAILY:
            payload['room_url'] = session.external_room_url
            payload['room_name'] = session.external_room_name
        return Response(payload)

    @action(detail=True, methods=['post'])
    def token(self, request, slug=None, *args, **kwargs):
        """Issue a short-lived signed viewer token for playback (MVP)."""
        session = self.get_object()
        streaming_payload = self._mint_streaming_token(session, request)
        if streaming_payload:
            return Response(streaming_payload)

        import jwt, time
        secret = getattr(__import__('django.conf').conf.settings, 'SECRET_KEY')
        payload = {
            'session_id': session.id,
            'session_slug': session.slug,
            'exp': int(time.time()) + 60 * 15,
        }
        token = jwt.encode(payload, secret, algorithm='HS256')
        return Response({'token': token, 'provider': session.provider})

    @action(detail=True, methods=['post'])
    def regenerate_key(self, request, slug=None, *args, **kwargs):
        """Regenerate the stream key (host only)."""
        session = self.get_object()
        if session.host != request.user:
            return Response({'error': 'Only host can regenerate stream key.'}, status=status.HTTP_403_FORBIDDEN)
        import secrets
        session.stream_key = secrets.token_urlsafe(32)
        session.save()
        return Response({'stream_key': session.stream_key})

    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, slug=None, *args, **kwargs):
        """Return paginated chat history for this live session.

        Accessible at: /api/live-sessions/<slug>/messages/
        """
        session = self.get_object()
        qs = LiveChatMessage.objects.filter(session=session).order_by('created_at')

        # Use the same pagination class as LiveChatViewSet if available
        paginator_cls = getattr(LiveChatViewSet, 'pagination_class', None)
        if paginator_cls:
            paginator = paginator_cls()
            page = paginator.paginate_queryset(qs, request, view=self)
            serializer = LiveChatMessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = LiveChatMessageSerializer(qs, many=True)
        return Response(serializer.data)


class LiveChatViewSet(viewsets.ModelViewSet):
    queryset = LiveChatMessage.objects.all().order_by('created_at')
    serializer_class = LiveChatMessageSerializer
    permission_classes = [IsAuthenticated]
    from rest_framework.pagination import PageNumberPagination
    class ChatPagination(PageNumberPagination):
        page_size = 25
        page_size_query_param = 'page_size'
        max_page_size = 100
    pagination_class = ChatPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        qs = LiveChatMessage.objects.all().order_by('created_at')
        session_id = self.request.query_params.get('session')
        if session_id:
            qs = qs.filter(session_id=session_id)
        return qs

    @action(detail=False, methods=['post'], url_path='suggest-by-budget', permission_classes=[IsAuthenticatedOrReadOnly])
    def suggest_by_budget(self, request):
        """Suggest recipes based on user budget. Does not disrupt ingredient-based suggestions."""
        # Handle both DRF requests and raw Django requests for testing
        if hasattr(request, 'data'):
            budget = request.data.get('budget')
        else:
            # Fallback for test requests
            import json
            try:
                if hasattr(request, 'body'):
                    data = json.loads(request.body.decode('utf-8'))
                    budget = data.get('budget')
                else:
                    budget = request.POST.get('budget')
            except (json.JSONDecodeError, AttributeError):
                budget = None
        
        if budget is None:
            return Response({'error': 'Budget is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            return Response({'error': 'Budget must be a number.'}, status=status.HTTP_400_BAD_REQUEST)

        # Assuming Recipe model has an 'estimated_cost' field
        from django.db.models import Q
        # Include recipes with missing cost (estimated_cost is null) as well as those within budget
        recipes = Recipe.objects.filter(Q(estimated_cost__lte=budget) | Q(estimated_cost__isnull=True), is_active=True)
        serializer = self.get_serializer(recipes, many=True)
        return Response({'suggested_recipes': serializer.data, 'info': f'Recipes under budget {budget} francs.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='search', permission_classes=[IsAuthenticatedOrReadOnly])
    def search_by_name(self, request):
        """Search recipes by title, description, ingredient, tag or cuisine. Returns paginated results and helpful suggestions when no matches found."""
        recipe_name = request.query_params.get('name', '').strip()
        if not recipe_name:
            return Response({'error': 'Please provide a recipe name to search for.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.db.models import Q

        # Search across multiple related fields (case-insensitive)
        queryset = Recipe.objects.filter(
            Q(title__icontains=recipe_name) |
            Q(description__icontains=recipe_name) |
            Q(ingredients__name__icontains=recipe_name) |
            Q(tags__name__icontains=recipe_name) |
            Q(cuisines__name__icontains=recipe_name),
            is_active=True
        ).distinct().order_by('title')

        # Paginate results to avoid huge responses
        paginator = SearchPagination()
        page = paginator.paginate_queryset(queryset, request)

        if not queryset.exists():
            # Provide fuzzy suggestions based on active recipe titles
            all_titles = list(Recipe.objects.filter(is_active=True).values_list('title', flat=True))
            # Use lowercase list for matching but return original-case titles
            lower_titles = [t.lower() for t in all_titles]
            suggestions_lower = get_close_matches(recipe_name.lower(), lower_titles, n=5, cutoff=0.6)
            suggestions = []
            for s in suggestions_lower:
                # map back to original casing (first match)
                for orig in all_titles:
                    if orig.lower() == s:
                        suggestions.append(orig)
                        break

            return Response({
                'count': 0,
                'results': [],
                'message': f'No recipes found matching "{recipe_name}"',
                'suggestions': suggestions
            }, status=status.HTTP_200_OK)

        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='suggest-by-ingredients')
    def suggest_by_ingredients(self, request):
        # Handle both DRF requests and raw Django requests for testing
        if hasattr(request, 'data'):
            ingredient_names = request.data.get('ingredient_names', [])
        else:
            # Fallback for test requests
            import json
            try:
                if hasattr(request, 'body'):
                    data = json.loads(request.body.decode('utf-8'))
                    ingredient_names = data.get('ingredient_names', [])
                else:
                    ingredient_names = request.POST.getlist('ingredient_names')
            except (json.JSONDecodeError, AttributeError):
                ingredient_names = []
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
                    'recipe': RecipeSerializer(recipe, context={'request': request}).data,
                    'missing_ingredients': [],
                    'message': 'You have all the ingredients for this meal!',
                    'substitutions': {}
                })
            elif len(user_ingredient_names & recipe_ingredient_names) >= 4:
                suggestions_list.append({
                    'recipe': RecipeSerializer(recipe, context={'request': request}).data,
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

    @action(detail=True, methods=['get'])
    def ratings(self, request, pk=None):
        """Return all ratings for a recipe."""
        recipe = self.get_object()
        ratings = recipe.rating_set.all()
        serializer = RecipeRatingSerializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Rate a recipe."""
        recipe = self.get_object()
        user = request.user
        
        # Check if user has already rated this recipe
        existing_rating = RecipeRating.objects.filter(user=user, recipe=recipe).first()
        
        if existing_rating:
            # Update existing rating
            serializer = RecipeRatingCreateSerializer(
                existing_rating,
                data=request.data,
                context={'request': request}
            )
        else:
            # Create new rating
            serializer = RecipeRatingCreateSerializer(
                data={**request.data, 'recipe': recipe.id},
                context={'request': request}
            )
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def likes(self, request, pk=None):
        """Return all likes for a recipe."""
        recipe = self.get_object()
        likes = recipe.like_set.all()
        serializer = RecipeLikeSerializer(likes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like or unlike a recipe."""
        recipe = self.get_object()
        user = request.user
        
        # Check if user has already liked this recipe
        existing_like = RecipeLike.objects.filter(user=user, recipe=recipe).first()
        
        if existing_like:
            # Unlike the recipe
            existing_like.delete()
            return Response({"status": "unliked"}, status=status.HTTP_200_OK)
        else:
            # Like the recipe
            serializer = RecipeLikeCreateSerializer(
                data={'recipe': recipe.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Return all approved comments for a recipe."""
        recipe = self.get_object()
        comments = recipe.comment_set.filter(is_approved=True)
        serializer = RecipeCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """Add a comment to a recipe."""
        recipe = self.get_object()
        
        serializer = RecipeCommentCreateSerializer(
            data={**request.data, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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


class IngredientPricePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class IngredientPriceViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Allow verified contributors and staff to manage ingredient prices and default weights."""

    serializer_class = IngredientPriceEntrySerializer
    permission_classes = [IsAuthenticated, IsVerifiedContributorOrStaff]
    parser_classes = [JSONParser]
    pagination_class = IngredientPricePagination
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        qs = Ingredient.objects.all().select_related('price').order_by('name')
        search = (self.request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(name__icontains=search)

        missing = (self.request.query_params.get('missing') or '').strip().lower()
        if missing == 'price':
            qs = qs.filter(Q(price__isnull=True) | Q(price__price_per_kg__isnull=True))
        elif missing == 'weight':
            qs = qs.filter(Q(default_unit_weight_g__isnull=True) | Q(default_unit_weight_g=0))
        elif missing in {'either', 'any'}:
            qs = qs.filter(
                Q(default_unit_weight_g__isnull=True) |
                Q(default_unit_weight_g=0) |
                Q(price__isnull=True) |
                Q(price__price_per_kg__isnull=True)
            )
        return qs


class IngredientPriceDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Simple HTML dashboard for editing ingredient prices via the API."""

    template_name = "pricing/ingredient_prices.html"

    def test_func(self):
        user = self.request.user
        return bool(getattr(user, 'is_verified_contributor', False) or user.is_staff)

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

class RecipeRatingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for recipe ratings.
    
    list:
    Return a list of all ratings for a specific recipe.
    
    create:
    Create a new rating for a recipe.
    
    retrieve:
    Return a specific rating.
    
    update:
    Update a specific rating.
    
    partial_update:
    Partially update a specific rating.
    
    destroy:
    Delete a specific rating.
    """
    queryset = RecipeRating.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeRatingCreateSerializer
        return RecipeRatingSerializer
    
    def get_queryset(self):
        """
        Filter ratings by recipe_id if provided in query parameters.
        """
        queryset = RecipeRating.objects.all()
        recipe_id = self.request.query_params.get('recipe_id', None)
        if recipe_id is not None:
            queryset = queryset.filter(recipe_id=recipe_id)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        """
        Only allow users to update or delete their own ratings.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()
        

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a rating to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


class RecipeLikeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for recipe likes.
    
    list:
    Return a list of all likes for a specific recipe.
    
    create:
    Like a recipe.
    
    retrieve:
    Return a specific like.
    
    destroy:
    Unlike a recipe.
    """
    queryset = RecipeLike.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return RecipeLikeCreateSerializer
        return RecipeLikeSerializer
    
    def get_queryset(self):
        """
        Filter likes by recipe_id if provided in query parameters.
        """
        queryset = RecipeLike.objects.all()
        recipe_id = self.request.query_params.get('recipe_id', None)
        if recipe_id is not None:
            queryset = queryset.filter(recipe_id=recipe_id)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        """
        Only allow users to delete their own likes.
        """
        if self.action in ['destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()


class RecipeCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for recipe comments.
    
    list:
    Return a list of all comments for a specific recipe.
    
    create:
    Create a new comment for a recipe.
    
    retrieve:
    Return a specific comment.
    
    update:
    Update a specific comment.
    
    partial_update:
    Partially update a specific comment.
    
    destroy:
    Delete a specific comment.
    """
    queryset = RecipeComment.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCommentCreateSerializer
        return RecipeCommentSerializer
    
    def get_queryset(self):
        """
        Filter comments by recipe_id if provided in query parameters.
        Only return approved comments unless the user is staff.
        """
        queryset = RecipeComment.objects.all()
        
        # Filter by recipe_id if provided
        recipe_id = self.request.query_params.get('recipe_id', None)
        if recipe_id is not None:
            queryset = queryset.filter(recipe_id=recipe_id)
        
        # Only show approved comments to non-staff users
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            queryset = queryset.filter(is_approved=True)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        """
        Only allow users to update or delete their own comments.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()