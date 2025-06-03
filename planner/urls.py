# planner/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MealPlanViewSet, NutritionInfoViewSet

router = DefaultRouter()
router.register(r'meal-plan', MealPlanViewSet, basename='meal-plan')
router.register(r'nutrition', NutritionInfoViewSet, basename='nutrition')

urlpatterns = [
    path('', include(router.urls)),
]
