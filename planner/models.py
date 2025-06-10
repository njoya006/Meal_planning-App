# planner/models.py

from django.db import models
from django.conf import settings

class MealPlan(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='meal_plans')
    recipe = models.ForeignKey('recipes.Recipe', on_delete=models.CASCADE, related_name='meal_plans')
    date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        unique_together = ('user', 'date', 'meal_type')
        verbose_name = 'Meal Plan'
        verbose_name_plural = 'Meal Plans'

    def clean(self):
        # Prevent more than one meal of the same type per user per day
        if MealPlan.objects.exclude(pk=self.pk).filter(user=self.user, date=self.date, meal_type=self.meal_type).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError('You already have a meal plan for this meal type on this date.')

    def __str__(self):
        return f"{self.user.username} - {self.recipe.title} ({self.meal_type}) on {self.date}"

class NutritionInfo(models.Model):
    """Stores detailed nutrition info for a recipe. Consider moving to recipes app for better domain logic."""
    recipe = models.OneToOneField('recipes.Recipe', on_delete=models.CASCADE, related_name='nutrition_info')
    calories = models.FloatField()
    protein = models.FloatField(help_text="Protein in grams")
    fat = models.FloatField(help_text="Fat in grams")
    carbs = models.FloatField(help_text="Carbohydrates in grams")
    fiber = models.FloatField(default=0, help_text="Fiber in grams")
    sugar = models.FloatField(default=0, help_text="Sugar in grams")
    sodium = models.FloatField(default=0, help_text="Sodium in mg")
    cholesterol = models.FloatField(default=0, help_text="Cholesterol in mg")
    # Add more micronutrients as needed
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nutrition for {self.recipe.name}"

class DietaryRule(models.Model):
    """Custom dietary rule for system-wide recommendations. Can be global or user-specific."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    include_ingredients = models.JSONField(blank=True, null=True, help_text="List of ingredient names to include")
    exclude_ingredients = models.JSONField(blank=True, null=True, help_text="List of ingredient names to exclude")
    min_ingredients = models.PositiveIntegerField(default=0, help_text="Minimum number of matching ingredients required")
    max_ingredients = models.PositiveIntegerField(default=0, help_text="Maximum number of matching ingredients allowed (0 = no limit)")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='custom_rules', help_text="If set, this rule is user-specific; otherwise, it's global.")
    priority = models.PositiveIntegerField(default=0, help_text="Higher priority rules are applied first.")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-priority', 'name']

    def __str__(self):
        return self.name

