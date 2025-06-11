from django.urls import path
from .views import (
    FavoriteRecipeListCreateView,
    FavoriteRecipeDestroyView,
    RecipeRatingListCreateView,
    RecipeRatingDetailView,
)

urlpatterns = [
    path('favorites/', FavoriteRecipeListCreateView.as_view(), name='favorite-recipes-list-create'),
    path('favorites/<int:pk>/', FavoriteRecipeDestroyView.as_view(), name='favorite-recipe-destroy'),
    path('ratings/', RecipeRatingListCreateView.as_view(), name='recipe-ratings-list-create'),
    path('ratings/<int:pk>/', RecipeRatingDetailView.as_view(), name='recipe-rating-detail'),
]
