from django import forms
from .models import Recipe

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe  # Specify the Recipe model
        fields = ['title', 'description', 'instructions', 'ingredients']  # Include fields for the form
        