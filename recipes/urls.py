from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r'', RecipeViewSet)  # Register at root for /api/recipes/
router.register(r'ingredients', IngredientViewSet)

urlpatterns = router.urls