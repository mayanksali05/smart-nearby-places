from flask import Blueprint, request, jsonify, current_app
from utils.distance import haversine_distance

import requests
from pymongo.errors import PyMongoError
from bson import ObjectId


places_bp = Blueprint("places", __name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
def serialize_place(place):
    if "_id" in place:
        place["_id"] = str(place["_id"])
    return place



@places_bp.route("/nearby", methods=["GET"])
def fetch_nearby_places():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    place_type = request.args.get("type", "restaurant")

    if not lat or not lng:
        return jsonify({"error": "lat and lng are required"}), 400

    query = f"""
    [out:json];
    node
      ["amenity"="{place_type}"]
      (around:2000,{lat},{lng});
    out;
    """

    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=25)

        if response.status_code == 200:
            data = response.json()

            places = []
            user_lat = float(lat)
            user_lng = float(lng)

            for element in data.get("elements", []):
                place_lat = element.get("lat")
                place_lon = element.get("lon")

                distance = haversine_distance(
                    user_lat, user_lng,
                    place_lat, place_lon
                )

                places.append({
                    "name": element.get("tags", {}).get("name", "Unknown"),
                    "type": place_type,
                    "lat": place_lat,
                    "lon": place_lon,
                    "distance_km": distance
                })


            if places:
                current_app.db.places.insert_many(places)

            return jsonify(places)

        # ❌ Overpass error → fallback
        raise Exception("Overpass timeout")

    except Exception:
        # ✅ FALLBACK TO MONGODB
        try:
            cached_places = list(
            current_app.db.places.find(
                {"type": place_type},
                {"_id": 0}
            ).limit(20)
        )

            user_lat = float(lat)
            user_lng = float(lng)

            for place in cached_places:
                place["distance_km"] = haversine_distance(
                    user_lat,
                    user_lng,
                    place["lat"],
                    place["lon"]
                )

            return jsonify({
            "source": "cache",
            "count": len(cached_places),
            "places": cached_places
        })


        except PyMongoError:
            return jsonify({
                "error": "Both Overpass and MongoDB failed"
            }), 503
