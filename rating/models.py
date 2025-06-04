from django.db import models
from django.contrib.auth import get_user_model

# Assuming 'Recipe' model will be provided by Dev 2 in their 'recipes' app
# You might need to import it like: from recipes.models import Recipe

User = get_user_model()

class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_recipes')
    recipe = models.ForeignKey('recipes.Recipe', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe') # A user can favorite a recipe only once
        verbose_name = "Favorite Recipe"
        verbose_name_plural = "Favorite Recipes"

    def _str_(self):
        return f"{self.user.username} favorited {self.recipe.title}"
class RecipeRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    recipe = models.ForeignKey('recipes.Recipe', on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)]) # 1 to 5 stars
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe') # A user can rate a recipe only once
        verbose_name = "Recipe Rating"
        verbose_name_plural = "Recipe Ratings"

    def _str_(self):
        return f"{self.user.username} rated {self.recipe.title} with {self.rating} stars"

