from django.contrib import admin
from .models import MealPlan, NutritionInfo, DietaryRule

# Register your models here.
@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'date', 'meal_type', 'created_at']
    search_fields = ['user__username', 'recipe__title']
    list_filter = ['meal_type', 'date']

admin.site.register(NutritionInfo)

@admin.register(DietaryRule)
class DietaryRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
