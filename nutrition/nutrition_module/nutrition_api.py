
"""Adapter for the USDA FoodData Central API."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_URL = "https://api.nal.usda.gov/fdc/v1"


def fetch_nutrition(ingredients, api_url=None, headers=None, timeout=15):
    """
    Search USDA FoodData Central for each ingredient.

    Args:
        ingredients: List of ingredient names or dictionaries with a 'name' field.
        api_url: Optional USDA API base URL.
        headers: Optional HTTP headers.
        timeout: Request timeout in seconds.

    Returns:
        Dictionary containing the USDA search results for each ingredient.

    Raises:
        ValueError: If ingredients, API URL, or API key is missing.
        RuntimeError: If a request fails or USDA returns invalid data.
    """
    if not ingredients:
        raise ValueError("At least one ingredient is required")

    api_key = os.getenv("NUTRITION_APP_KEY")
    if not api_key:
        raise ValueError("NUTRITION_APP_KEY is missing from the environment")

    base_url = (
        api_url
        or os.getenv("NUTRITION_API_URL")
        or DEFAULT_API_URL
    ).rstrip("/")

    search_url = f"{base_url}/foods/search"
    results = []

    for ingredient in ingredients:
        if isinstance(ingredient, str):
            ingredient_name = ingredient.strip()
        elif isinstance(ingredient, dict):
            ingredient_name = str(ingredient.get("name", "")).strip()
        else:
            raise ValueError(
                "Each ingredient must be a string or a dictionary"
            )

        if not ingredient_name:
            raise ValueError("Ingredient name cannot be empty")

        params = {
            "api_key": api_key,
            "query": ingredient_name,
            "pageSize": 1,
        }

        try:
            response = requests.get(
                search_url,
                params=params,
                headers=headers or {},
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()

        except requests.Timeout as exc:
            raise RuntimeError(
                f"USDA request timed out for: {ingredient_name}"
            ) from exc

        except requests.RequestException as exc:
            raise RuntimeError(
                f"USDA request failed for: {ingredient_name}"
            ) from exc

        except ValueError as exc:
            raise RuntimeError(
                f"USDA returned invalid JSON for: {ingredient_name}"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError("USDA returned an unexpected response")

        foods = data.get("foods", [])

        if not foods:
            results.append(
                {
                    "ingredient": ingredient_name,
                    "found": False,
                    "food": None,
                }
            )
            continue

        food = foods[0]

        results.append(
            {
                "ingredient": ingredient_name,
                "found": True,
                "food": {
                    "fdcId": food.get("fdcId"),
                    "description": food.get("description"),
                    "dataType": food.get("dataType"),
                    "foodNutrients": food.get("foodNutrients", []),
                },
            }
        )

    return {"results": results}

