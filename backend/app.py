from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

from config import Config

def create_app():
    app = Flask(__name__)
    CORS(app)

    # MongoDB connection
    client = MongoClient(Config.MONGO_URI)
    app.db = client[Config.DB_NAME]

    # Register blueprints
    from services.places_api import places_bp
    from services.interactions_api import interactions_bp

    app.register_blueprint(places_bp, url_prefix="/api/places")
    app.register_blueprint(interactions_bp, url_prefix="/api/interactions")



    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
