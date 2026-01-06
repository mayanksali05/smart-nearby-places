from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

interactions_bp = Blueprint("interactions", __name__)

@interactions_bp.route("/log", methods=["POST"])
def log_interaction():
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    interaction = {
        "user_id": data.get("user_id", "anonymous"),
        "place_id": data.get("place_id"),
        "action": data.get("action"),
        "category": data.get("category"),
        "timestamp": datetime.utcnow()
    }

    if not interaction["place_id"] or not interaction["action"]:
        return jsonify({"error": "place_id and action are required"}), 400

    current_app.db.user_interactions.insert_one(interaction)

    return jsonify({"status": "logged"})
