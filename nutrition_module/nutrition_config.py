"""Load Nutrition API configuration from the environment."""

import os

from dotenv import load_dotenv

load_dotenv()

NUTRITION_APP_ID = os.getenv("NUTRITION_APP_ID")
NUTRITION_APP_KEY = os.getenv("NUTRITION_APP_KEY")
NUTRITION_API_URL = os.getenv("NUTRITION_API_URL")
