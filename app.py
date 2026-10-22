from flask import Flask, jsonify, redirect, request

from config import Config
from routes.auth_routes import auth_bp
from routes.chat_routes import chat_bp
from routes.recipe_routes import generate_recipe_route, recipe_bp
from routes.view_routes import view_bp
from services.vegetable_service import classifier_service
from nutrition_module.nutrition_service import analyze_recipe

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(auth_bp)
    app.register_blueprint(recipe_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(view_bp)

    @app.get("/")
    def index():
        return redirect("/login")

    @app.post("/api/identify-vegetable")
    def identify_vegetable():
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image file provided in request."}), 400

        file = request.files["image"]
        if not file or not file.filename:
            return jsonify({"success": False, "error": "No image file selected."}), 400

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"Invalid file type. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            }), 400

        try:
            result = classifier_service.predict(file.stream)
            return jsonify({
                "success": True,
                "data": {
                    "vegetable": result["label"],
                    "confidence": result["confidence"],
                },
            }), 200
        except Exception as exc:
            return jsonify({
                "success": False,
                "error": f"Failed to identify vegetable: {str(exc)}",
            }), 500

    @app.post("/api/nutrition/analyze")
    def analyze_nutrition_route():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"success": False, "error": "Request body must be valid JSON."}), 400

        ingredients = data.get("ingredients")
        servings = data.get("servings")

        if not isinstance(ingredients, list) or len(ingredients) == 0:
            return jsonify({"success": False, "error": "Ingredients must be a non-empty list."}), 400

        if isinstance(servings, bool) or not isinstance(servings, int) or servings <= 0:
            return jsonify({"success": False, "error": "Servings must be an integer greater than 0."}), 400

        try:
            result = analyze_recipe(ingredients, servings)
            return jsonify({"success": True, "data": result}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
