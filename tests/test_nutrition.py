"""Module-level tests for nutrition calculation and the API adapter.

API calls are fully mocked. These tests never contact a live service.
"""

from unittest.mock import Mock

import pytest
import requests

from nutrition_module.nutrition_api import fetch_nutrition
from nutrition_module.nutrition_calculator import (
    calculate_per_serving,
    calculate_total_nutrition,
)
from nutrition_module.nutrition_service import analyze_recipe


@pytest.fixture
def sample_ingredients():
    return [
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


def test_total_nutrition(sample_ingredients):
    result = calculate_total_nutrition(sample_ingredients)
    assert result["calories"] == 300
    assert result["protein"] == 8
    assert result["carbohydrates"] == 45
    assert result["fat"] == 9
    assert result["fiber"] == 6
    assert result["sugar"] == 4


def test_per_serving_calculation():
    totals = {
        "calories": 300,
        "protein": 8,
        "carbohydrates": 45,
        "fat": 9,
        "fiber": 6,
        "sugar": 4,
    }
    result = calculate_per_serving(totals, 2)
    assert result["calories"] == 150
    assert result["protein"] == 4
    assert result["carbohydrates"] == 22.5
    assert result["fat"] == 4.5
    assert result["fiber"] == 3
    assert result["sugar"] == 2


def test_single_serving(sample_ingredients):
    result = analyze_recipe(sample_ingredients, 1)
    assert result["per_serving"]["calories"] == 300


def test_multiple_servings():
    totals = {
        "calories": 900,
        "protein": 9,
        "carbohydrates": 90,
        "fat": 9,
        "fiber": 6,
        "sugar": 3,
    }
    result = calculate_per_serving(totals, 3)
    assert result["calories"] == 300
    assert result["protein"] == 3
    assert result["carbohydrates"] == 30


def test_empty_ingredients():
    with pytest.raises(ValueError):
        analyze_recipe([], 2)


@pytest.mark.parametrize("servings", [0, -1, True, 1.5, False, "2"])
def test_invalid_servings(servings):
    with pytest.raises(ValueError):
        calculate_per_serving(
            {"calories": 300},
            servings,
        )


def test_missing_nutrient_treated_as_zero():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {
                "calories": 80,
                "protein": 2,
            },
        }
    ]
    result = calculate_total_nutrition(ingredients)
    assert result["calories"] == 80
    assert result["protein"] == 2
    assert result["carbohydrates"] == 0
    assert result["fat"] == 0
    assert result["fiber"] == 0
    assert result["sugar"] == 0


def test_none_nutrient_treated_as_zero():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {
                "calories": 40,
                "sugar": None,
            },
        }
    ]
    result = calculate_total_nutrition(ingredients)
    assert result["calories"] == 40
    assert result["sugar"] == 0


def test_negative_nutrient_value():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {"calories": -100},
        }
    ]
    with pytest.raises(ValueError):
        calculate_total_nutrition(ingredients)


def test_invalid_nutrient_type():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {"protein": "unknown"},
        }
    ]
    with pytest.raises(ValueError):
        calculate_total_nutrition(ingredients)


def test_boolean_nutrient_rejected():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {"calories": True},
        }
    ]
    with pytest.raises(ValueError):
        calculate_total_nutrition(ingredients)


def test_non_finite_nutrient_rejected():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {"fat": float("nan")},
        }
    ]
    with pytest.raises(ValueError):
        calculate_total_nutrition(ingredients)


def test_totals_rounded_to_two_decimal_places():
    ingredients = [
        {
            "name": "Ingredient A",
            "nutrition": {"calories": 0.004, "protein": 1.226},
        },
        {
            "name": "Ingredient B",
            "nutrition": {"calories": 0.004, "protein": 1.226},
        },
    ]
    result = calculate_total_nutrition(ingredients)
    assert result["calories"] == 0.01
    assert result["protein"] == 2.45


def test_analyze_recipe_sample_output(sample_ingredients):
    result = analyze_recipe(sample_ingredients, servings=2)
    assert result["total_nutrition"] == {
        "calories": 300.0,
        "protein": 8.0,
        "carbohydrates": 45.0,
        "fat": 9.0,
        "fiber": 6.0,
        "sugar": 4.0,
    }
    assert result["per_serving"] == {
        "calories": 150.0,
        "protein": 4.0,
        "carbohydrates": 22.5,
        "fat": 4.5,
        "fiber": 3.0,
        "sugar": 2.0,
    }
    assert result["servings"] == 2
    assert result["units"] == {
        "calories": "kcal",
        "protein": "g",
        "carbohydrates": "g",
        "fat": "g",
        "fiber": "g",
        "sugar": "g",
    }


def test_empty_api_url():
    with pytest.raises(ValueError):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="",
        )


def test_empty_api_ingredients():
    with pytest.raises(ValueError):
        fetch_nutrition(
            [],
            api_url="https://example.com/nutrition",
        )


def test_api_timeout(monkeypatch):
    def mock_post(*args, **kwargs):
        raise requests.Timeout("Timed out")

    monkeypatch.setattr(requests, "post", mock_post)
    with pytest.raises(RuntimeError, match="timed out"):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="https://example.com/nutrition",
        )


def test_api_http_error(monkeypatch):
    response = Mock()
    response.raise_for_status.side_effect = requests.HTTPError("HTTP 500")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: response,
    )
    with pytest.raises(RuntimeError, match="request failed"):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="https://example.com/nutrition",
        )


def test_api_connection_error(monkeypatch):
    def mock_post(*args, **kwargs):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(requests, "post", mock_post)
    with pytest.raises(RuntimeError, match="request failed"):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="https://example.com/nutrition",
        )


def test_api_invalid_json(monkeypatch):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("Invalid JSON")
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: response,
    )
    with pytest.raises(RuntimeError, match="invalid JSON"):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="https://example.com/nutrition",
        )


def test_api_json_decode_error(monkeypatch):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = requests.exceptions.JSONDecodeError(
        "Expecting value",
        "not-json",
        0,
    )
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: response,
    )
    with pytest.raises(RuntimeError, match="invalid JSON"):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="https://example.com/nutrition",
        )


def test_api_non_object_response(monkeypatch):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = ["not", "an", "object"]
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: response,
    )
    with pytest.raises(RuntimeError, match="unexpected response"):
        fetch_nutrition(
            ["100 g ingredient"],
            api_url="https://example.com/nutrition",
        )


def test_api_success(monkeypatch):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "calories": 150,
        "protein": 4,
    }
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: response,
    )
    result = fetch_nutrition(
        ["100 g ingredient"],
        api_url="https://example.com/nutrition",
    )
    assert result["calories"] == 150
    assert result["protein"] == 4
