"""
recipes/bad_ingredients.py

This module provides dynamic access to bad ingredient pairs, triplets, and categories for meal suggestion filtering.
All data is now managed via the BadIngredient model in the database and can be updated via the Django admin.

Usage:
- Use get_bad_ingredient_pairs(), get_bad_ingredient_triplets(), and get_bad_ingredient_categories() to retrieve the latest data.
- Ingredient substitutions remain static for now, but can be made dynamic in the future.
"""

from .models import BadIngredient, IngredientSubstitution
from collections import defaultdict

# Dynamic accessors for bad ingredient pairs, triplets, and categories

def get_bad_ingredient_pairs():
    """Return a set of sorted tuples (ingredient1, ingredient2) for bad pairs."""
    pairs = set()
    for obj in BadIngredient.objects.filter(type='pair'):
        items = sorted([i.strip().lower() for i in obj.ingredients.split(',') if i.strip()])
        if len(items) == 2:
            pairs.add(tuple(items))
    return pairs

def get_bad_ingredient_triplets():
    """Return a set of sorted tuples (ingredient1, ingredient2, ingredient3) for bad triplets."""
    triplets = set()
    for obj in BadIngredient.objects.filter(type='triplet'):
        items = sorted([i.strip().lower() for i in obj.ingredients.split(',') if i.strip()])
        if len(items) == 3:
            triplets.add(tuple(items))
    return triplets

def get_bad_ingredient_categories():
    """Return a dict mapping category name to a set of ingredient names."""
    categories = defaultdict(set)
    for obj in BadIngredient.objects.filter(type='category'):
        cat = obj.category.strip().lower() if obj.category else 'uncategorized'
        items = [i.strip().lower() for i in obj.ingredients.split(',') if i.strip()]
        categories[cat].update(items)
    return dict(categories)

def get_ingredient_substitutions():
    """Return a dict mapping ingredient name to a list of substitutions from the database."""
    subs = {}
    for obj in IngredientSubstitution.objects.all():
        subs[obj.ingredient.strip().lower()] = obj.substitutions
    return subs
