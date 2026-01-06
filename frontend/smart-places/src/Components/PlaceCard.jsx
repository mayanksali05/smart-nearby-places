import { logInteraction } from "../api";

export default function PlaceCard({ place }) {
  const handleClick = () => {
    logInteraction({
      user_id: "anon_user",
      place_id: place.osm_id,
      action: "click",
      category: place.type
    });
  };

  return (
    <div className="place-card" onClick={handleClick}>
      <h4>{place.name}</h4>
      <p>📍 Distance: {place.distance_km.toFixed(2)} km</p>
      <p>⭐ Score: {place.score.toFixed(2)}</p>
    </div>
  );
}
