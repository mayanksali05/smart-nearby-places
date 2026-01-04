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
    place_type = request.args.get("type", "restaurant")
    radius = int(request.args.get("radius", 5000))  # meters

    if not lat or not lng:
        return jsonify({"error": "lat and lng are required"}), 400

    user_lat = float(lat)
    user_lng = float(lng)
    radius_km = radius / 1000

    city = get_city_from_latlng(lat, lng)

    query = f"""
    [out:json];
    node
      ["amenity"~"restaurant|fast_food|cafe|food_court|bar|hotel"]
      (around:{radius},{lat},{lng});
    out;
    """

    try:
        response = requests.post(OVERPASS_URL, data=query, timeout=30)
        response.raise_for_status()
        data = response.json()

        places = []
        for el in data.get("elements", []):
            place_lat = el.get("lat")
            place_lon = el.get("lon")

            distance_km = haversine_distance(
                user_lat, user_lng, place_lat, place_lon
            )

            # 🔑 HARD RADIUS FILTER
            if distance_km > radius_km:
                continue

            places.append({
                "osm_id": el.get("id"),
                "name": el.get("tags", {}).get("name", "Unknown"),
                "type": place_type,
                "lat": place_lat,
                "lon": place_lon,
                "lat_bucket": round(place_lat, 1),
                "lng_bucket": round(place_lon, 1),
                "city": city
            })

        # Upsert filtered places only
        for place in places:
            current_app.db.places.update_one(
                {"osm_id": place["osm_id"]},
                {"$set": place},
                upsert=True
            )

        return jsonify({
            "city": city,
            "radius_m": radius,
            "count": len(places),
            "places": places
        })

    except Exception:
        # -------- FALLBACK (CACHE) --------
        try:
            lat_bucket = round(user_lat, 1)
            lng_bucket = round(user_lng, 1)

            cached = list(
                current_app.db.places.find(
                    {
                        "type": place_type,
                        "lat_bucket": lat_bucket,
                        "lng_bucket": lng_bucket
                    },
                    {"_id": 0}
                )
            )

            results = []
            for place in cached:
                dist = haversine_distance(
                    user_lat, user_lng, place["lat"], place["lon"]
                )
                if dist <= radius_km:
                    place["distance_km"] = dist
                    results.append(place)

            return jsonify({
                "source": "cache",
                "city": city,
                "radius_m": radius,
                "count": len(results),
                "places": results
            })

        except PyMongoError:
            return jsonify({"error": "Both Overpass and MongoDB failed"}), 503


@places_bp.route("/recommend", methods=["GET"])
def recommend():
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    place_type = request.args.get("type", "restaurant")
    top_n = int(request.args.get("top_n", 10))
    radius = int(request.args.get("radius", 5000))  # meters

    if not lat or not lng:
        return jsonify({"error": "lat and lng are required"}), 400

    user_lat = float(lat)
    user_lng = float(lng)
    radius_km = radius / 1000

    lat_bucket = round(user_lat, 1)
    lng_bucket = round(user_lng, 1)

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
        return jsonify({"error": "No cached places for this location"}), 404

    # Deduplicate
    unique = {}
    for p in places:
        key = p.get("osm_id") or f"{p['lat']}_{p['lon']}_{p['name']}"
        unique[key] = p

    filtered = []
    for place in unique.values():
        dist = haversine_distance(
            user_lat, user_lng, place["lat"], place["lon"]
        )
        if dist <= radius_km:
            place["distance_km"] = dist
            filtered.append(place)

    recommended = recommend_places(filtered, top_n=top_n)

    return jsonify({
        "radius_m": radius,
        "count": len(recommended),
        "recommendations": recommended
    })

