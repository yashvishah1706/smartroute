import { useEffect, useMemo, useState, useCallback } from "react";
import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from "react-leaflet";

const CENTER = [40.741, -74.029];
const formatMeters = (m) => (m >= 1000 ? `${(m/1000).toFixed(2)} km` : `${(m||0).toFixed(0)} m`);
const formatMinutes = (s) => (s ? `${(s/60).toFixed(1)} min` : "–");

function FitToRoute({ feature }) {
  const map = useMap();
  useEffect(() => {
    if (!feature?.geometry?.coordinates?.length) return;
    const latlngs = feature.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
    map.fitBounds(latlngs, { padding: [40, 40] });
  }, [feature, map]);
  return null;
}

export default function RouteMap() {
  const [feature, setFeature] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    origin_lat: 40.742,
    origin_lon: -74.032,
    dest_lat: 40.735,
    dest_lon: -74.027,
    place: "Hoboken, New Jersey, USA",
    algo: "dijkstra",
    weight: "distance",          // NEW
    avoid_highways: false,       // NEW
  });

  const origin = useMemo(() => [Number(form.origin_lat), Number(form.origin_lon)], [form]);
  const dest   = useMemo(() => [Number(form.dest_lat),  Number(form.dest_lon)],  [form]);

  const fetchRoute = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const params = new URLSearchParams({
        origin_lat: form.origin_lat,
        origin_lon: form.origin_lon,
        dest_lat: form.dest_lat,
        dest_lon: form.dest_lon,
        place: form.place,
        algo: form.algo,
        weight: form.weight,                                   // NEW
        avoid_highways: String(form.avoid_highways),           // NEW
      });
      const res = await fetch(`http://127.0.0.1:5000/route-geojson?${params.toString()}`);
      if (!res.ok) throw new Error(`Backend ${res.status}`);
      setFeature(await res.json());
    } catch (e) { console.error(e); setError("Failed to fetch route."); }
    finally { setLoading(false); }
  }, [form]);

  useEffect(() => { fetchRoute(); }, []); // initial

  const onOriginDragEnd = (e) => {
    const { lat, lng } = e.target.getLatLng();
    setForm((f) => ({ ...f, origin_lat: lat.toFixed(6), origin_lon: lng.toFixed(6) }));
  };
  const onDestDragEnd = (e) => {
    const { lat, lng } = e.target.getLatLng();
    setForm((f) => ({ ...f, dest_lat: lat.toFixed(6), dest_lon: lng.toFixed(6) }));
  };
  useEffect(() => { const t = setTimeout(fetchRoute, 300); return () => clearTimeout(t); },
    [form.origin_lat, form.origin_lon, form.dest_lat, form.dest_lon]); // drag auto-recalc

  const distance = feature?.properties?.distance_m;
  const duration = feature?.properties?.duration_s;
  const props = feature?.properties;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", height: "100vh" }}>
      <div style={{ padding: 12, borderRight: "1px solid #eee" }}>
        <h2 style={{ marginTop: 0 }}>SmartRoute</h2>
        <div style={{ fontSize: 13, marginBottom: 10, color: "#aaa" }}>
          Drag the pins or edit the inputs, then compute.
        </div>

        <label>Place</label>
        <input style={{ width: "100%", marginBottom: 8 }} value={form.place}
               onChange={(e) => setForm({ ...form, place: e.target.value })} />

        <label>Origin (lat, lon)</label>
        <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
          <input style={{ width: "50%" }} value={form.origin_lat}
                 onChange={(e) => setForm({ ...form, origin_lat: e.target.value })}/>
          <input style={{ width: "50%" }} value={form.origin_lon}
                 onChange={(e) => setForm({ ...form, origin_lon: e.target.value })}/>
        </div>

        <label>Destination (lat, lon)</label>
        <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
          <input style={{ width: "50%" }} value={form.dest_lat}
                 onChange={(e) => setForm({ ...form, dest_lat: e.target.value })}/>
          <input style={{ width: "50%" }} value={form.dest_lon}
                 onChange={(e) => setForm({ ...form, dest_lon: e.target.value })}/>
        </div>

        <label>Algorithm</label>
        <select style={{ width: "100%", marginBottom: 8 }} value={form.algo}
                onChange={(e) => setForm({ ...form, algo: e.target.value })}>
          <option value="dijkstra">Dijkstra</option>
          <option value="astar">A*</option>
        </select>

        <label>Weight</label> {/* NEW */}
        <select style={{ width: "100%", marginBottom: 8 }} value={form.weight}
                onChange={(e) => setForm({ ...form, weight: e.target.value })}>
          <option value="distance">Shortest distance</option>
          <option value="time">Fastest time</option>
        </select>

        <label style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
          <input type="checkbox" checked={form.avoid_highways}
                 onChange={(e) => setForm({ ...form, avoid_highways: e.target.checked })}/>
          Avoid highways
        </label>

        <button onClick={fetchRoute} disabled={loading} style={{ width: "100%", marginBottom: 8 }}>
          {loading ? "Computing..." : "Compute Route"}
        </button>

        {error && <div style={{ color: "#ff6b6b", fontSize: 13 }}>{error}</div>}

        <div style={{ marginTop: 10, padding: 10, border: "1px solid #333", borderRadius: 8, fontSize: 14 }}>
          <div><strong>Distance:</strong> {formatMeters(distance)}</div>
          <div><strong>ETA:</strong> {formatMinutes(duration)}</div>
          <div><strong>Algorithm:</strong> {props?.algorithm ?? form.algo}</div>
          <div><strong>Weight:</strong> {props?.weight ?? form.weight}</div>
          <div><strong>Avoid highways:</strong> {String(props?.avoid_highways ?? form.avoid_highways)}</div>
          <div><strong>Nodes:</strong> {props?.nodes ?? "-"}</div>
        </div>
      </div>

      <MapContainer center={CENTER} zoom={14} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {feature && <GeoJSON key={Date.now()} data={feature} style={{ weight: 5 }} />}
        <Marker position={origin} draggable eventHandlers={{ dragend: (e)=>onOriginDragEnd(e) }}>
          <Popup>Origin<br/>{origin[0].toFixed(5)}, {origin[1].toFixed(5)}</Popup>
        </Marker>
        <Marker position={dest} draggable eventHandlers={{ dragend: (e)=>onDestDragEnd(e) }}>
          <Popup>Destination<br/>{dest[0].toFixed(5)}, {dest[1].toFixed(5)}</Popup>
        </Marker>
        <FitToRoute feature={feature} />
      </MapContainer>
    </div>
  );
}
