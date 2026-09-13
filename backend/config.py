import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "aurora"
GOOGLE_VISION_KEY_PATH = os.getenv("GOOGLE_VISION_KEY_PATH")
