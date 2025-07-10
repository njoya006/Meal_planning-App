
from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import RecipeViewSet, IngredientViewSet, RecipeRatingViewSet, RecipeLikeViewSet, RecipeCommentViewSet, RecipeReviewsView

router = DefaultRouter()
router.register(r'', RecipeViewSet)  # Register at root for /api/recipes/
router.register(r'ingredients', IngredientViewSet)
router.register(r'ratings', RecipeRatingViewSet)
router.register(r'likes', RecipeLikeViewSet)
router.register(r'comments', RecipeCommentViewSet)

# Place the custom reviews path BEFORE the router's URLs
urlpatterns = [
    path('<int:pk>/reviews/', RecipeReviewsView.as_view(), name='recipe-reviews'),
] + router.urls