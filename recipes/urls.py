from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = router.urls