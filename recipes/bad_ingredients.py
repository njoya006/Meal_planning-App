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
from functools import lru_cache


# Dynamic accessors for bad ingredient pairs, triplets, and categories.
# The BadIngredient model stores a JSONField `ingredients` (list of names)
# and a `type` field that can be 'pair', 'combination' (triplet), or 'category'.


def _normalize_name(n):
    try:
        return n.strip().lower()
    except Exception:
        return str(n).strip().lower()


@lru_cache(maxsize=1)
def get_bad_ingredient_pairs():
    """Return a set of sorted 2-tuples for bad ingredient pairs.

    Example: {('fish', 'milk'), ...}
    """
    pairs = set()
    for obj in BadIngredient.objects.filter(type__in=['pair']):
        items = obj.ingredients or []
        if not isinstance(items, (list, tuple)):
            # Defensive: if stored as comma string, split
            try:
                items = [i.strip() for i in str(items).split(',') if i.strip()]
            except Exception:
                items = []
        items = [_normalize_name(i) for i in items if i]
        if len(items) == 2:
            pairs.add(tuple(sorted(items)))
    return pairs


@lru_cache(maxsize=1)
def get_bad_ingredient_triplets():
    """Return a set of sorted 3-tuples for bad ingredient triplets/combination.

    The model sometimes uses type='combination' for triplets.
    """
    triplets = set()
    for obj in BadIngredient.objects.filter(type__in=['triplet', 'combination']):
        items = obj.ingredients or []
        if not isinstance(items, (list, tuple)):
            try:
                items = [i.strip() for i in str(items).split(',') if i.strip()]
            except Exception:
                items = []
        items = [_normalize_name(i) for i in items if i]
        if len(items) >= 3:
            # If more than 3 given, only consider combinations of length 3
            # but store exact sorted tuple when exactly 3
            if len(items) == 3:
                triplets.add(tuple(sorted(items)))
            else:
                # For longer lists, add all 3-combinations
                from itertools import combinations
                for comb in combinations(sorted(items), 3):
                    triplets.add(tuple(comb))
    return triplets


@lru_cache(maxsize=1)
def get_bad_ingredient_categories():
    """Return a dict mapping category name to a set of ingredient names.

    Uses the BadIngredient.description field (if provided) as category name; fallback
    to 'category' or 'uncategorized'.
    """
    categories = defaultdict(set)
    for obj in BadIngredient.objects.filter(type__in=['category']):
        cat = None
        try:
            cat = (obj.description or '').strip().lower()
        except Exception:
            cat = None
        if not cat:
            # Fallback to using a generic label if not provided
            cat = 'category'
        items = obj.ingredients or []
        if not isinstance(items, (list, tuple)):
            try:
                items = [i.strip() for i in str(items).split(',') if i.strip()]
            except Exception:
                items = []
        for i in items:
            if not i:
                continue
            categories[cat].add(_normalize_name(i))
    return dict(categories)


@lru_cache(maxsize=1)
def get_ingredient_substitutions():
    """Return a dict mapping ingredient name to a list of substitutions from IngredientSubstitution model."""
    subs = {}
    for obj in IngredientSubstitution.objects.all():
        try:
            key = _normalize_name(obj.ingredient)
            values = obj.substitutions or []
            if not isinstance(values, (list, tuple)):
                try:
                    values = [v.strip() for v in str(values).split(',') if v.strip()]
                except Exception:
                    values = []
            subs[key] = [ _normalize_name(v) for v in values if v ]
        except Exception:
            continue
    return subs
