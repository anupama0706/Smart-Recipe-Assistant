"""Aggregate ingredient nutrition into recipe totals and per-serving values."""

import math

NUTRIENT_KEYS = [
    "calories",
    "protein",
    "carbohydrates",
    "fat",
    "fiber",
    "sugar",
]


def _coerce_nutrient(value, key):
    """Return a finite, non-negative float for one nutrient.

    Missing values (None) follow the module policy and count as zero.
    Booleans are rejected even though bool is a subclass of int.
    """
    if value is None:
        return 0.0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Invalid nutritional value for {key}")
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError(f"Invalid nutritional value for {key}")
    return numeric


def calculate_total_nutrition(ingredients):
    """Calculate total nutrition from ingredient-level values.

    Each ingredient must contain a 'nutrition' dictionary
    with values for the supported nutrients. Missing nutrient
    values are treated as zero. Totals are rounded to 2 decimal places.
    """
    totals = {key: 0.0 for key in NUTRIENT_KEYS}

    for ingredient in ingredients:
        if not isinstance(ingredient, dict):
            raise ValueError("Invalid nutritional value for ingredient")
        nutrition = ingredient.get("nutrition") or {}
        if not isinstance(nutrition, dict):
            raise ValueError("Invalid nutritional value for nutrition")
        for key in NUTRIENT_KEYS:
            totals[key] += _coerce_nutrient(nutrition.get(key, 0), key)

    return {key: round(value, 2) for key, value in totals.items()}


def calculate_per_serving(total_nutrition, servings):
    """Calculate approximate nutritional values per serving.

    Results are rounded to 2 decimal places. Servings must be a
    positive integer. Booleans, non-integers, and values <= 0 are rejected.
    """
    if (
        isinstance(servings, bool)
        or not isinstance(servings, int)
        or servings <= 0
    ):
        raise ValueError("Servings must be a positive integer")

    per_serving = {}
    for key, value in total_nutrition.items():
        per_serving[key] = round(_coerce_nutrient(value, key) / servings, 2)
    return per_serving
