import io
import unittest
from PIL import Image

from app import create_app


class VegetableApiStandaloneTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def test_identify_vegetable_endpoint(self):
        # 1. Create a synthetic test image using PIL (RGB, 224x224, solid green)
        image = Image.new("RGB", (224, 224), color=(34, 139, 34))

        # 2. Save it temporarily as an in-memory BytesIO object
        image_bytes = io.BytesIO()
        image.save(image_bytes, format="PNG")
        image_bytes.seek(0)

        # 3. Use Flask test client to send a POST request with the test image payload
        response = self.client.post(
            "/api/identify-vegetable",
            data={"image": (image_bytes, "synthetic_veg.png")},
            content_type="multipart/form-data",
        )

        # 4. Assert that the response HTTP status code is 200
        self.assertEqual(response.status_code, 200)

        # 5. Assert that returned JSON payload contains "success": true and non-empty "vegetable" and "confidence" fields
        payload = response.get_json()
        self.assertIsNotNone(payload)
        self.assertIs(payload.get("success"), True)
        self.assertIn("data", payload)

        data = payload["data"]
        self.assertTrue(bool(data.get("vegetable")))
        self.assertIsNotNone(data.get("confidence"))
        self.assertGreaterEqual(float(data["confidence"]), 0.0)


if __name__ == "__main__":
    unittest.main()
