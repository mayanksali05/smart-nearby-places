from flask import Blueprint, request, jsonify, current_app
import requests
from pymongo.errors import PyMongoError
from bson import ObjectId


from utils.distance import haversine_distance
from ml.recommender import recommend_places

places_bp = Blueprint("places", __name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def serialize_place(place):
    if "_id" in place:
        place["_id"] = str(place["_id"])
    return place


def get_city_from_latlng(lat, lng):
    params = {
        "lat": lat,
        "lon": lng,
        "format": "json"
    }
    headers = {
        "User-Agent": "smart-nearby-places-app"
    }

    try:
        res = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if res.status_code == 200:
            address = res.json().get("address", {})
            return (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
            )
    except Exception:
        pass

    return "Unknown"




@places_bp.route("/nearby", methods=["GET"])
def fetch_nearby_places():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    city = get_city_from_latlng(lat, lng)
    place_type = request.args.get("type", "restaurant")

    if not lat or not lng:
        return jsonify({"error": "lat and lng are required"}), 400

    query = f"""
        [out:json];
        node
        ["amenity"~"restaurant|fast_food|cafe|food_court|bar|hotel"]
        (around:10000,{lat},{lng});
        out;
        """


    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=25)

        if response.status_code == 200:
            data = response.json()

            places = []
            for element in data.get("elements", []):
                place_lat = element.get("lat")
                place_lon = element.get("lon")

                places.append({
                    "osm_id": element.get("id"),
                    "name": element.get("tags", {}).get("name", "Unknown"),
                    "type": place_type,
                    "lat": place_lat,
                    "lon": place_lon,
                    "lat_bucket": round(place_lat, 1),
                    "lng_bucket": round(place_lon, 1),
                    "city": city
                })



            # ✅ correct upsert
            for place in places:
                current_app.db.places.update_one(
                    {"osm_id": place["osm_id"]},
                    {"$set": place},
                    upsert=True
                )

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


@places_bp.route("/recommend", methods=["GET"])
def recommend():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    place_type = request.args.get("type", "restaurant")
    top_n = int(request.args.get("top_n", 10))

    if not lat or not lng:
        return jsonify({"error": "lat and lng are required"}), 400

    user_lat = float(lat)
    user_lng = float(lng)

    # 🔑 LOCATION BUCKETS (FIX OPTION 2)
    lat_bucket = round(user_lat, 1)
    lng_bucket = round(user_lng, 1)

    # ✅ location-aware cache query
    places = list(
        current_app.db.places.find(
            {
                "type": place_type,
                "lat_bucket": lat_bucket,
                "lng_bucket": lng_bucket
            },
            {"_id": 0}
        )
    )

    if not places:
        return jsonify({
            "error": "No places available for this location",
            "lat_bucket": lat_bucket,
            "lng_bucket": lng_bucket
        }), 404

    # 🔁 deduplicate safely
    unique_places = {}
    for place in places:
        key = place.get("osm_id") or f"{place['lat']}_{place['lon']}_{place['name']}"
        unique_places[key] = place

    places = list(unique_places.values())

    # 📏 attach distance dynamically
    for place in places:
        place["distance_km"] = haversine_distance(
            user_lat,
            user_lng,
            place["lat"],
            place["lon"]
        )

    # ⭐ recommendation scoring
    recommended = recommend_places(places, top_n=top_n)

    return jsonify({
        "count": len(recommended),
        "recommendations": recommended
    })

