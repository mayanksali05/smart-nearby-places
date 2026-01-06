from ml.features import build_features

def score_place(place, user_pref=None):
    score = 0

    distance = place.get("distance_km", 5)
    rating = place.get("rating", 3.5)
    popularity = place.get("popularity", 10)
    category = place.get("type", "unknown")

    score += max(0, 5 - distance) * 2
    score += rating * 1.5
    score += popularity * 0.1

    if user_pref and category in user_pref:
        score += 3

    return score


def recommend_places(places, top_n=10, user_pref=None):
    for place in places:
        place["score"] = score_place(place, user_pref)

    places.sort(key=lambda x: x["score"], reverse=True)
    return places[:top_n]
