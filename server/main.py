# server/main.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from graph_engine import (
    load_graph,
    get_shortest_route,
    route_to_geojson_feature,
)

# ---- Flask app setup -------------------------------------------------
load_dotenv()
app = Flask(__name__)
CORS(app)  # allow requests from the Vite dev server

# ---- Health check ----------------------------------------------------
@app.route("/")
def home():
    return jsonify({"message": "SmartRoute Flask server running"}), 200


# ---- Helpers: distance & time accumulation ---------------------------
def route_length_meters(G, route_nodes):
    """
    Sum edge 'length' along a list of nodes in a (MultiDi)Graph.
    For parallel edges, pick the shortest length.
    """
    total = 0.0
    for u, v in zip(route_nodes[:-1], route_nodes[1:]):
        edge_dict = G.get_edge_data(u, v)
        if not edge_dict:
            continue
        best = None
        for _, data in edge_dict.items():
            L = data.get("length")
            if L is not None:
                best = L if best is None else min(best, L)
        if best is not None:
            total += float(best)
    return total


def route_travel_time_seconds(G, route_nodes):
    """
    Sum edge 'travel_time' (seconds) if present.
    For parallel edges, pick the shortest travel_time.
    """
    total = 0.0
    for u, v in zip(route_nodes[:-1], route_nodes[1:]):
        edge_dict = G.get_edge_data(u, v)
        if not edge_dict:
            continue
        best = None
        for _, data in edge_dict.items():
            tt = data.get("travel_time")
            if tt is not None:
                best = tt if best is None else min(best, tt)
        if best is not None:
            total += float(best)
    return total


# ---- Demo route (optional quick sanity check) ------------------------
@app.route("/test-route")
def test_route():
    # small area = faster first load
    place = "Hoboken, New Jersey, USA"
    G = load_graph(place)
    origin = (40.742, -74.032)       # (lat, lon)
    dest   = (40.735, -74.027)

    nodes = get_shortest_route(
        G, origin, dest,
        algorithm="dijkstra",
        weight_mode="distance",
        avoid_highways=False,
    )

    return jsonify({
        "algorithm": "dijkstra",
        "total_nodes": len(nodes),
        "total_distance_m": route_length_meters(G, nodes),
        "route_nodes": nodes,
    }), 200


# ---- Main API: GeoJSON line with properties -------------------------
@app.route("/route-geojson")
def route_geojson_api():
    try:
        place = request.args.get("place", "Hoboken, New Jersey, USA")
        algo = request.args.get("algo", "dijkstra").lower()
        weight_mode = request.args.get("weight", "distance").lower()  # 'distance' | 'time'
        avoid = request.args.get("avoid_highways", "false").lower() in {"1", "true", "yes"}

        o_lat = float(request.args["origin_lat"])
        o_lon = float(request.args["origin_lon"])
        d_lat = float(request.args["dest_lat"])
        d_lon = float(request.args["dest_lon"])

        G = load_graph(place)
        nodes = get_shortest_route(
            G, (o_lat, o_lon), (d_lat, d_lon),
            algorithm=algo,
            weight_mode=weight_mode,
            avoid_highways=avoid,
        )

        dist_m = route_length_meters(G, nodes)
        # Only sum time if we routed in 'time' mode (edges will have travel_time)
        time_s = route_travel_time_seconds(G, nodes) if weight_mode == "time" else 0.0

        feature = route_to_geojson_feature(
            G, nodes,
            props={
                "algorithm": algo,
                "weight": weight_mode,
                "avoid_highways": avoid,
                "distance_m": dist_m,
                "duration_s": time_s,
                "nodes": len(nodes),
            },
        )
        return jsonify(feature), 200

    except KeyError as e:
        return jsonify({"error": f"missing required query param: {str(e)}"}), 400
    except Exception as e:
        # surface the error during dev
        return jsonify({"error": f"internal error: {str(e)}"}), 500


# ---- Entrypoint ------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
