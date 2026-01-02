def compute_score(place):
    """
    Higher score = better recommendation
    """
    distance = place.get("distance_km", 999)
    return round(1 / (distance + 0.1), 4)


def recommend_places(places, top_n=10):
    for place in places:
        place["score"] = compute_score(place)

    # sort by score (descending)
    places.sort(key=lambda x: x["score"], reverse=True)

    return places[:top_n]
