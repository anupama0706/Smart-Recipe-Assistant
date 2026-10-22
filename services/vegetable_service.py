import json
import os
from pathlib import Path
import numpy as np
from PIL import Image

try:
    import keras
except ImportError:
    from tensorflow import keras


class VegetableClassifierService:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(VegetableClassifierService, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_path=None, class_names_path=None):
        if self._initialized:
            return

        base_dir = Path(__file__).resolve().parent.parent

        if model_path is None:
            candidate_paths = [
                base_dir / "models" / "vegetable_mobilenetv2.keras",
                Path("models/vegetable_mobilenetv2.keras"),
                base_dir / "smart-recipe-assistant" / "models" / "vegetable_mobilenetv2.keras",
            ]
            for candidate in candidate_paths:
                if candidate.exists():
                    model_path = candidate
                    break
            if model_path is None:
                model_path = candidate_paths[0]

        if class_names_path is None:
            candidate_class_paths = [
                base_dir / "models" / "class_names.json",
                Path("models/class_names.json"),
                base_dir / "smart-recipe-assistant" / "models" / "class_names.json",
            ]
            for candidate in candidate_class_paths:
                if candidate.exists():
                    class_names_path = candidate
                    break
            if class_names_path is None:
                class_names_path = candidate_class_paths[0]

        self.model_path = Path(model_path)
        self.class_names_path = Path(class_names_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found at {self.model_path}")
        if not self.class_names_path.exists():
            raise FileNotFoundError(f"Class names file not found at {self.class_names_path}")

        with open(self.class_names_path, "r", encoding="utf-8") as f:
            self.class_names = json.load(f)

        self.model = keras.saving.load_model(str(self.model_path))
        self._initialized = True

    def predict(self, file_stream):
        """
        Converts image stream to 224x224 RGB, converts to float32 NumPy array in [0, 255] range,
        expands the batch dimension, runs model.predict(), and returns:
        {"label": predicted_label, "confidence": round(confidence * 100, 2)}
        """
        if hasattr(file_stream, "seek"):
            try:
                file_stream.seek(0)
            except Exception:
                pass

        image = Image.open(file_stream)
        image = image.convert("RGB")
        image = image.resize((224, 224))

        arr = np.array(image, dtype=np.float32)
        arr = np.expand_dims(arr, axis=0)

        predictions = self.model.predict(arr, verbose=0)
        idx = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][idx])
        predicted_label = self.class_names[idx]

        return {
            "label": predicted_label,
            "confidence": round(confidence * 100, 2),
        }


classifier_service = VegetableClassifierService()
