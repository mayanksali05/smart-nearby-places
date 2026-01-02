import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME", "smart_nearby_places")
    # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
