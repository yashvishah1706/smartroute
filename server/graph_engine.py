import osmnx as ox
import networkx as nx
from typing import List, Tuple, Dict, Any

_GRAPH_CACHE = {}

# --------- version-safe helpers ----------
def _add_edge_lengths_compat(G):
    if hasattr(ox, "distance") and hasattr(ox.distance, "add_edge_lengths"):
        return ox.distance.add_edge_lengths(G)
    if hasattr(ox, "add_edge_lengths"):
        return ox.add_edge_lengths(G)
    if hasattr(ox, "utils_graph") and hasattr(ox.utils_graph, "add_edge_lengths"):
        return ox.utils_graph.add_edge_lengths(G)
    return G

def _nearest_nodes_compat(G, lon, lat):
    if hasattr(ox, "distance") and hasattr(ox.distance, "nearest_nodes"):
        return ox.distance.nearest_nodes(G, lon, lat)
    if hasattr(ox, "nearest_nodes"):
        return ox.nearest_nodes(G, lon, lat)
    raise RuntimeError("No nearest_nodes function found in this OSMnx version.")
# -----------------------------------------

def load_graph(place: str):
    """Load/cached drivable graph for place."""
    if place in _GRAPH_CACHE:
        return _GRAPH_CACHE[place]
    G = ox.graph_from_place(place, network_type='drive')
    G = _add_edge_lengths_compat(G)
    _GRAPH_CACHE[place] = G
    return G

# --- speed defaults (km/h) if maxspeed missing ---
DEFAULT_SPEEDS_KMH: Dict[str, float] = {
    "motorway": 100, "trunk": 80, "primary": 60, "secondary": 50, "tertiary": 40,
    "unclassified": 35, "residential": 30, "living_street": 15, "service": 20
}

def _parse_maxspeed_kmh(val) -> float | None:
    """Handle '30', '30 mph', ['30','40'], etc."""
    if val is None:
        return None
    if isinstance(val, list) and val:
        val = val[0]
    try:
        s = str(val).lower().strip()
        if "mph" in s:
            num = float(s.split("mph")[0].strip())
            return num * 1.60934
        return float(''.join(ch for ch in s if (ch.isdigit() or ch == '.')))
    except Exception:
        return None

def _edge_speed_kmh(data: Dict[str, Any]) -> float:
    # 1) use maxspeed if available
    ms = _parse_maxspeed_kmh(data.get("maxspeed"))
    if ms:
        return ms
    # 2) otherwise infer from 'highway' tag
    hw = data.get("highway")
    if isinstance(hw, list) and hw:
        hw = hw[0]
    return DEFAULT_SPEEDS_KMH.get(str(hw), 40.0)

def _apply_edge_time(G):
    """Add 'travel_time' (seconds) to each edge based on length/maxspeed."""
    for u, v, k, data in G.edges(keys=True, data=True):
        length_m = float(data.get("length", 0.0))
        speed_kmh = _edge_speed_kmh(data)
        speed_mps = speed_kmh * 1000 / 3600.0
        tt = length_m / speed_mps if speed_mps > 0 else 0.0
        data["travel_time"] = tt
    return G

def _filtered_graph(G, avoid_highways: bool):
    """Optionally remove motorway/motorway_link when user avoids highways."""
    if not avoid_highways:
        return G
    remove_edges = []
    for u, v, k, d in G.edges(keys=True, data=True):
        hw = d.get("highway")
        if isinstance(hw, list): hw = hw[0]
        if str(hw) in {"motorway", "motorway_link"}:
            remove_edges.append((u, v, k))
    H = G.copy()
    H.remove_edges_from(remove_edges)
    return H

def get_shortest_route(
    G,
    origin_point: Tuple[float, float],
    destination_point: Tuple[float, float],
    algorithm: str = 'dijkstra',
    weight_mode: str = 'distance',   # 'distance' or 'time'
    avoid_highways: bool = False
) -> List[int]:
    """
    Compute path between (lat, lon) points using chosen weight & flags.
    """
    o_lat, o_lon = origin_point
    d_lat, d_lon = destination_point
    origin_node = _nearest_nodes_compat(G, o_lon, o_lat)
    destination_node = _nearest_nodes_compat(G, d_lon, d_lat)

    # choose graph & weight
    H = _filtered_graph(G, avoid_highways)
    weight = 'length' if weight_mode == 'distance' else 'travel_time'
    if weight == 'travel_time':
        _apply_edge_time(H)

    if algorithm == 'dijkstra':
        return nx.shortest_path(H, origin_node, destination_node, weight=weight)
    elif algorithm == 'astar':
        return nx.astar_path(H, origin_node, destination_node, weight=weight)
    else:
        raise ValueError("Algorithm must be 'dijkstra' or 'astar'.")

def route_nodes_to_coords(G, route_nodes: List[int]):
    coords = []
    for nid in route_nodes:
        node = G.nodes[nid]
        coords.append([float(node['x']), float(node['y'])])  # [lon, lat]
    return coords

def route_to_geojson_feature(G, route_nodes: List[int], props: Dict[str, Any] | None = None):
    coords = route_nodes_to_coords(G, route_nodes)
    return {
        "type": "Feature",
        "properties": props or {},
        "geometry": {"type": "LineString", "coordinates": coords}
    }
