from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import RecipeViewSet, IngredientViewSet, RecipeRatingViewSet, RecipeLikeViewSet, RecipeCommentViewSet, RecipeReviewsView
from .views import LiveSessionViewSet, LiveChatViewSet, IngredientPriceViewSet

router = DefaultRouter()
router.register(r'', RecipeViewSet, basename='recipe')  # Register at root for /api/recipes/ (explicit basename)
router.register(r'ingredients', IngredientViewSet)
router.register(r'ingredient-prices', IngredientPriceViewSet, basename='ingredient-price')
router.register(r'ratings', RecipeRatingViewSet)
router.register(r'likes', RecipeLikeViewSet)
router.register(r'comments', RecipeCommentViewSet)
router.register(r'live-sessions', LiveSessionViewSet, basename='live-session')
router.register(r'live-chat', LiveChatViewSet, basename='live-chat')

# Place the custom reviews path BEFORE the router's URLs
urlpatterns = [
    path('<int:pk>/reviews/', RecipeReviewsView.as_view(), name='recipe-reviews'),
] + router.urls