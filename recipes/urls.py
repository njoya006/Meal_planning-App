from django.urls import path
from . import views
from .views import RecipeCreateView, UserRecipesView

urlpatterns = [
    path('', views.recipes_list, name='recipe_list'),
    path('<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('create/', views.recipe_create, name='recipe_create'),
    path('<int:pk>/update/', views.recipe_update, name='recipe_update'),
    path('<int:pk>/delete/', views.recipe_delete, name='recipe_delete'),
    path('suggest/', views.recipe_suggest, name='recipe_suggest'),
    # API endpoints
    path('api/create/', RecipeCreateView.as_view(), name='api_recipe_create'),
    path('api/my/', UserRecipesView.as_view(), name='api_user_recipes'),
]
