import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RECIPES_PATH = DATA_DIR / "recipes.json"

_RECIPES_CACHE: Optional[List[Dict[str, Any]]] = None


def normalize_ingredient(name: str) -> str:
    """Normalize ingredient name for robust fuzzy/token matching."""
    if not name:
        return ""
    text = str(name).strip().lower()
    text = text.replace("_", " ")
    text = re.sub(r"[^\w\s]", "", text)
    tokens = text.split()
    normalized_tokens = []
    ignore_words = {"fresh", "raw", "diced", "chopped", "sliced", "boiled", "peeled", "cut", "minced"}
    for token in tokens:
        if token in ignore_words and len(tokens) > 1:
            continue
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("es") and len(token) > 3 and token not in ("cheese",):
            token = token[:-2]
        elif token.endswith("s") and len(token) > 2 and not token.endswith("ss") and token not in ("rasam", "hummus"):
            token = token[:-1]
        normalized_tokens.append(token)
    result = " ".join(normalized_tokens)
    return result if result else text


def _extract_ingredient_name(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("name", "")).strip()
    return str(item).strip()


def load_recipes() -> List[Dict[str, Any]]:
    """Load recipes from data/recipes.json with caching."""
    global _RECIPES_CACHE
    if _RECIPES_CACHE is not None:
        return _RECIPES_CACHE

    paths_to_try = [
        RECIPES_PATH,
        Path("data/recipes.json"),
        Path(__file__).resolve().parent.parent / "smart-recipe-assistant" / "data" / "recipes.json",
    ]

    for path in paths_to_try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _RECIPES_CACHE = json.load(f)
                return _RECIPES_CACHE

    _RECIPES_CACHE = []
    return _RECIPES_CACHE


def get_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    """Look up a recipe by its ID."""
    recipes = load_recipes()
    target = str(recipe_id).strip().lower()
    for r in recipes:
        if str(r.get("id", "")).strip().lower() == target:
            return r
    return None


def get_recipe_by_name(dish_name: str) -> Optional[Dict[str, Any]]:
    """Look up a recipe by dish name."""
    recipes = load_recipes()
    target = normalize_ingredient(dish_name)
    for r in recipes:
        r_name = normalize_ingredient(r.get("name", ""))
        if target == r_name or target in r_name or r_name in target:
            return r
    return None


def match_recipes(available_ingredients: List[Any]) -> List[Dict[str, Any]]:
    """
    Computes:
    Match Percentage = (len(available_ingredients ∩ required_ingredients) / len(required_ingredients)) * 100.
    Sorts matching recipes by match_percentage descending, then total time ascending.
    Returns matched and missing ingredient lists.
    """
    recipes = load_recipes()
    if not available_ingredients:
        available_ingredients = []

    normalized_available = [
        normalize_ingredient(_extract_ingredient_name(item))
        for item in available_ingredients
        if item
    ]
    normalized_available = [item for item in normalized_available if item]

    recommendations = []

    for recipe in recipes:
        required_raw = recipe.get("required_ingredients", [])
        total_required = len(required_raw)
        matched_ingredients = []
        missing_ingredients = []

        for req in required_raw:
            req_name = _extract_ingredient_name(req)
            norm_req = normalize_ingredient(req_name)

            is_matched = False
            for avail in normalized_available:
                if norm_req == avail or norm_req in avail or avail in norm_req:
                    is_matched = True
                    break

            if is_matched:
                matched_ingredients.append(req_name)
            else:
                missing_ingredients.append(req_name)

        if total_required > 0:
            match_percentage = round((len(matched_ingredients) / total_required) * 100, 1)
        else:
            match_percentage = 0.0

        prep_time = int(recipe.get("prep_time_minutes", 0))
        cook_time = int(recipe.get("cook_time_minutes", 0))
        total_time = prep_time + cook_time

        item_result = {
            "id": recipe.get("id"),
            "name": recipe.get("name"),
            "cuisine": recipe.get("cuisine"),
            "prep_time_minutes": prep_time,
            "cook_time_minutes": cook_time,
            "total_time_minutes": total_time,
            "servings": recipe.get("servings", 4),
            "match_percentage": match_percentage,
            "matched_ingredients": matched_ingredients,
            "missing_ingredients": missing_ingredients,
            "required_ingredients": required_raw,
            "pantry_staples": recipe.get("pantry_staples", []),
            "base_instructions": recipe.get("base_instructions", []),
        }
        recommendations.append(item_result)

    # Sort descending by match percentage, then total time ascending
    recommendations.sort(key=lambda r: (-r["match_percentage"], r["total_time_minutes"]))
    return recommendations
