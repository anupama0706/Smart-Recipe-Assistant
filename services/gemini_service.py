import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv()

try:
    from google import genai
    from google.genai import errors, types
except ImportError:
    genai = None
    types = None
    errors = None

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

COMMON_STAPLE_SUBSTITUTIONS = {
    "tomato": ("Tamarind paste or amchur with a splash of lemon", "Provides required acidity and tang"),
    "potato": ("Sweet potato, raw banana, or cauliflower florets", "Provides starchy body and bulk"),
    "onion": ("Asafoetida (hing) or finely shredded cabbage", "Replaces savory allium aroma"),
    "ginger": ("Dry ginger powder (sonth)", "Adds pungent warmth"),
    "garlic": ("Asafoetida (hing) or garlic powder", "Replaces pungent depth"),
    "cauliflower": ("Broccoli florets or cabbage wedges", "Similar texture and vegetable sweetness"),
    "carrot": ("Pumpkin or sweet potato cubes", "Provides color and sweetness"),
    "brinjal": ("Zucchini or roasted mushroom cubes", "Absorbs spices and provides tender texture"),
    "capsicum": ("Green chili or mild paprika", "Subtle pepper note"),
}


def _graceful_fallback(
    recipe: Dict[str, Any],
    missing_ingredients: List[Any],
    reason: str = "Fallback mode",
) -> Dict[str, Any]:
    """Generates standard household staple substitutions and returns base instructions."""
    substitutions = []
    for item in (missing_ingredients or []):
        name = item.get("name", "") if isinstance(item, dict) else str(item)
        norm = name.strip().lower()
        sub_info = None
        for k, val in COMMON_STAPLE_SUBSTITUTIONS.items():
            if k in norm or norm in k:
                sub_info = val
                break

        if sub_info:
            sub_name, sub_notes = sub_info
        else:
            sub_name = f"Use equivalent pantry vegetables or spices, or omit {name}"
            sub_notes = "Common household pantry substitute."

        substitutions.append({
            "missing_ingredient": name,
            "substitute": sub_name,
            "notes": sub_notes,
        })

    return {
        "recipe_id": recipe.get("id"),
        "substitutions": substitutions,
        "instructions": recipe.get("base_instructions", []),
        "fallback": True,
        "notes": f"Using base instructions ({reason}).",
    }


def adapt_recipe_instructions(
    recipe: Dict[str, Any],
    available_ingredients: Optional[List[Any]] = None,
    missing_ingredients: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Accepts recipe, available_ingredients, and missing_ingredients.
    Uses the google-genai SDK to generate:
      a) Common household substitutions for missing items.
      b) Adapted step-by-step cooking instructions.
    If GEMINI_API_KEY is not configured or an API error / quota limit occurs,
    gracefully falls back to returning the recipe's static base_instructions
    and common staple substitutions without raising an HTTP 500 error.
    """
    if available_ingredients is None:
        available_ingredients = []
    if missing_ingredients is None:
        missing_ingredients = []

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    # Graceful fallback when API key is not present or invalid test placeholder
    if not api_key or api_key in ("dummy-key-for-test", "your-api-key-here") or genai is None:
        return _graceful_fallback(recipe, missing_ingredients, reason="GEMINI_API_KEY not configured")

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert chef assistant specializing in Indian and home-style cuisine.
Recipe: {recipe.get('name')}
Cuisine: {recipe.get('cuisine', 'Indian')}
Base Ingredients: {recipe.get('required_ingredients')}
Pantry Staples: {recipe.get('pantry_staples')}
Base Instructions: {recipe.get('base_instructions')}

Available Ingredients in User Kitchen: {available_ingredients}
Missing Ingredients: {missing_ingredients}

Please generate:
1. Common household culinary substitutions for each missing ingredient.
2. Adapted step-by-step cooking instructions customized for the available ingredients and suggested substitutions.

Return ONLY a valid JSON object matching this schema:
{{
  "substitutions": [
    {{
      "missing_ingredient": "string",
      "substitute": "string",
      "notes": "string"
    }}
  ],
  "instructions": [
    "string"
  ]
}}
"""
        config = None
        if types and hasattr(types, "GenerateContentConfig"):
            config = types.GenerateContentConfig(response_mime_type="application/json")

        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=config,
        )

        text = (response.text or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        parsed = json.loads(text)
        instructions = parsed.get("instructions") or recipe.get("base_instructions", [])
        substitutions = parsed.get("substitutions") or []

        return {
            "recipe_id": recipe.get("id"),
            "substitutions": substitutions,
            "instructions": instructions,
            "fallback": False,
        }
    except Exception as exc:
        err_msg = str(exc)
        return _graceful_fallback(recipe, missing_ingredients, reason=f"Gemini service notice: {err_msg}")
