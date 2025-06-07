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
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='meal_plans')
    date = models.DateField()
    meal_type = models.CharField(max_length=10, choices=MEAL_TYPES)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.meal_type} on {self.date}"

class Recipe(models.Model):
    name = models.CharField(max_length=255)
    # Add more fields as needed

    def __str__(self):
        return self.name

class NutritionInfo(models.Model):
    recipe = models.OneToOneField('Recipe', on_delete=models.CASCADE, related_name='nutrition_info')
    calories = models.FloatField()
    protein = models.FloatField(help_text="Protein in grams")
    fat = models.FloatField(help_text="Fat in grams")
    carbs = models.FloatField(help_text="Carbohydrates in grams")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nutrition for {self.recipe.name}"

