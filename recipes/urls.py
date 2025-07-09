from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, IngredientViewSet, RecipeRatingViewSet, RecipeLikeViewSet, RecipeCommentViewSet

router = DefaultRouter()
router.register(r'', RecipeViewSet)  # Register at root for /api/recipes/
router.register(r'ingredients', IngredientViewSet)
router.register(r'ratings', RecipeRatingViewSet)
router.register(r'likes', RecipeLikeViewSet)
router.register(r'comments', RecipeCommentViewSet)

urlpatterns = router.urls