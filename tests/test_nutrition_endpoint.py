import unittest
from app import create_app


class NutritionEndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def test_invalid_json_body(self):
        response = self.client.post("/api/nutrition/analyze", data="not json", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_missing_or_empty_ingredients(self):
        for payload in [{"servings": 2}, {"ingredients": [], "servings": 2}, {"ingredients": "apple", "servings": 2}]:
            response = self.client.post("/api/nutrition/analyze", json=payload)
            self.assertEqual(response.status_code, 400)
            self.assertFalse(response.get_json()["success"])

    def test_invalid_servings(self):
        sample = [{"name": "A", "nutrition": {"calories": 100}}]
        for invalid_servings in [0, -1, "2", True, False, None]:
            response = self.client.post("/api/nutrition/analyze", json={"ingredients": sample, "servings": invalid_servings})
            self.assertEqual(response.status_code, 400)
            self.assertFalse(response.get_json()["success"])

    def test_valid_nutrition_analysis(self):
        payload = {
            "ingredients": [
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
            ],
            "servings": 2,
        }
        response = self.client.post("/api/nutrition/analyze", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["servings"], 2)
        self.assertEqual(data["data"]["total_nutrition"]["calories"], 300)
        self.assertEqual(data["data"]["per_serving"]["calories"], 150)

    def test_internal_error_handling(self):
        from unittest.mock import patch
        with patch("app.analyze_recipe", side_effect=RuntimeError("Computation error")):
            response = self.client.post(
                "/api/nutrition/analyze",
                json={"ingredients": [{"name": "X"}], "servings": 2}
            )
            self.assertEqual(response.status_code, 500)
            data = response.get_json()
            self.assertFalse(data["success"])
            self.assertIn("Computation error", data["error"])


if __name__ == "__main__":
    unittest.main()
