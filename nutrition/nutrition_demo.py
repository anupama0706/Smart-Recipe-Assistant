"""Run the sample recipe used to verify the calculator and service."""

from nutrition_module.nutrition_service import analyze_recipe

ingredients = [
    {
        "name": "Ingredient A",
        "nutrition": {
            "calories": 200,
            "protein": 5,
            "carbohydrates": 30,
            "fat": 7,
            "fiber": 4,
            "sugar": 3,
        },
    },
    {
        "name": "Ingredient B",
        "nutrition": {
            "calories": 100,
            "protein": 3,
            "carbohydrates": 15,
            "fat": 2,
            "fiber": 2,
            "sugar": 1,
        },
    },
]

result = analyze_recipe(ingredients, servings=2)
print(result)
