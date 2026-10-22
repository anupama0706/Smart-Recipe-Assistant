import io
import unittest
from unittest.mock import patch
from PIL import Image

from app import create_app
from services.vegetable_service import VegetableClassifierService, classifier_service


def _create_dummy_image_stream(format="PNG", color=(100, 150, 50)):
    image = Image.new("RGB", (300, 300), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


class VegetableServiceTests(unittest.TestCase):
    def test_singleton_pattern(self):
        service1 = VegetableClassifierService()
        service2 = VegetableClassifierService()
        self.assertIs(service1, service2)
        self.assertIs(service1, classifier_service)

    def test_predict_returns_expected_structure(self):
        stream = _create_dummy_image_stream()
        result = classifier_service.predict(stream)

        self.assertIn("label", result)
        self.assertIn("confidence", result)
        self.assertIsInstance(result["label"], str)
        self.assertIn(result["label"], classifier_service.class_names)
        self.assertIsInstance(result["confidence"], float)


class VegetableEndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.client = self.app.test_client()

    def test_missing_image_file_returns_400(self):
        response = self.client.post("/api/identify-vegetable", data={})
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertIn("error", json_data)

    def test_empty_filename_returns_400(self):
        data = {"image": (io.BytesIO(b""), "")}
        response = self.client.post(
            "/api/identify-vegetable",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])

    def test_disallowed_extension_returns_400(self):
        data = {"image": (io.BytesIO(b"dummy text"), "test.txt")}
        response = self.client.post(
            "/api/identify-vegetable",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        json_data = response.get_json()
        self.assertFalse(json_data["success"])
        self.assertIn("Invalid file type", json_data["error"])

    def test_valid_image_identification_returns_200(self):
        stream = _create_dummy_image_stream(format="JPEG")
        data = {"image": (stream, "broccoli.jpg")}
        response = self.client.post(
            "/api/identify-vegetable",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data["success"])
        self.assertIn("data", json_data)
        self.assertIn("vegetable", json_data["data"])
        self.assertIn("confidence", json_data["data"])
        self.assertIsInstance(json_data["data"]["vegetable"], str)
        self.assertIsInstance(json_data["data"]["confidence"], float)

    def test_prediction_failure_returns_500(self):
        stream = _create_dummy_image_stream(format="PNG")
        data = {"image": (stream, "test.png")}
        with patch.object(classifier_service, "predict", side_effect=RuntimeError("Model failure")):
            response = self.client.post(
                "/api/identify-vegetable",
                data=data,
                content_type="multipart/form-data"
            )
            self.assertEqual(response.status_code, 500)
            json_data = response.get_json()
            self.assertFalse(json_data["success"])
            self.assertIn("Failed to identify vegetable", json_data["error"])


if __name__ == "__main__":
    unittest.main()
