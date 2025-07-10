from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import RecipeViewSet, IngredientViewSet, RecipeRatingViewSet, RecipeLikeViewSet, RecipeCommentViewSet, RecipeReviewsView

router = DefaultRouter()
router.register(r'', RecipeViewSet)  # Register at root for /api/recipes/
router.register(r'ingredients', IngredientViewSet)
router.register(r'ratings', RecipeRatingViewSet)
router.register(r'likes', RecipeLikeViewSet)
router.register(r'comments', RecipeCommentViewSet)

urlpatterns = router.urls + [
    # /api/recipes/<id>/reviews/
    path('recipes/<int:pk>/reviews/', RecipeReviewsView.as_view(), name='recipe-reviews'),
]