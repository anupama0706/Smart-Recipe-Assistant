"""Coordinate nutrition totals and per-serving values for a recipe."""

from nutrition_module.nutrition_calculator import (
    calculate_per_serving,
    calculate_total_nutrition,
)


def analyze_recipe(ingredients, servings):
    """Analyze a recipe using normalized ingredient nutrition data.

    This function is independent of the external API.
    Each ingredient must include nutritional values for
    its complete quantity used in the recipe.
    """
    if not ingredients:
        raise ValueError("Recipe must contain ingredients")

    total_nutrition = calculate_total_nutrition(ingredients)
    per_serving = calculate_per_serving(total_nutrition, servings)

    return {
        "total_nutrition": total_nutrition,
        "per_serving": per_serving,
        "servings": servings,
        "units": {
            "calories": "kcal",
            "protein": "g",
            "carbohydrates": "g",
            "fat": "g",
            "fiber": "g",
            "sugar": "g",
        },
    }
