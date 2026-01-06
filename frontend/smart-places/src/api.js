const BASE_URL = "http://127.0.0.1:5000/api";

export async function fetchNearby({ lat, lng, type }) {
  const url = `${BASE_URL}/places/nearby?lat=${lat}&lng=${lng}&type=${type}&radius=5000`;
  const res = await fetch(url);
  return res.json();
}

export async function getRecommendations({ lat, lng, type }) {
  const url = `${BASE_URL}/places/recommend?lat=${lat}&lng=${lng}&type=${type}&top_n=5`;
  const res = await fetch(url);
  return res.json();
}

export async function logInteraction(data) {
  await fetch(`${BASE_URL}/interactions/log`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
}
