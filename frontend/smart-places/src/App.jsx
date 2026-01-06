import { useState } from "react";
import { fetchNearby, getRecommendations } from "./api";
import PlaceCard from "./Components/PlaceCard";
import "./App.css";

export default function App() {
  const [lat, setLat] = useState("22.3072");
  const [lng, setLng] = useState("73.1812");
  const [type, setType] = useState("restaurant");
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const fetchPlaces = async () => {
    try {
      setLoading(true);
      setStatus("Fetching nearby places...");

      // 1️⃣ Warm up cache
      await fetchNearby({ lat, lng, type });

      setStatus("Ranking recommendations...");

      // 2️⃣ Get recommendations
      const data = await getRecommendations({ lat, lng, type });
      setPlaces(data.recommendations || []);
      setStatus("");

    } catch (err) {
      setStatus("Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <h2>📍 Smart Nearby Places</h2>

      <div className="form">
        <input value={lat} onChange={(e) => setLat(e.target.value)} />
        <input value={lng} onChange={(e) => setLng(e.target.value)} />

        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="restaurant">Restaurant</option>
          <option value="cafe">Cafe</option>
        </select>

        <button onClick={fetchPlaces} disabled={loading}>
          {loading ? "Please wait..." : "Get Recommendations"}
        </button>
      </div>

      {status && <p style={{ textAlign: "center" }}>{status}</p>}

      <div className="place-list">
        {places.map((p) => (
          <PlaceCard key={p.osm_id} place={p} />
        ))}
      </div>
    </div>
  );
}
