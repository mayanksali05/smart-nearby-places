def build_features(place, user_lat, user_lng):
    return {
        "distance": place.get("distance", 5),
        "rating": place.get("rating", 3.5),
        "popularity": place.get("popularity", 10),
        "category": place.get("category", "unknown")
    }
