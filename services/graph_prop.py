import networkx as nx
import json

# Load RE scores from batch
with open('data/sample_events.json') as f:
    events = json.load(f)

services_re = {}
for e in events:
    # Mock/stub RE (replace with real if saved)
    services_re[e["service"]] = sum([e["oss"], e["sts"], e["bcs"]]) / 3  # Avg

G = nx.DiGraph()
services = list(services_re.keys())[:6]  # Use real services

# Dynamic edges
G.add_edges_from([
    ("frontend", "api"), ("api", "auth"), 
    ("api", "db"), ("db", "cache")
])

def propagate_risk(G, services_re):
    risk_map = {}
    for node in nx.topological_sort(G):
        direct = services_re.get(node, 0)
        propagated = sum(risk_map.get(pred, 0) * 0.3 for pred in G.predecessors(node))
        risk_map[node] = min(1.0, direct + propagated)
    return risk_map

print("📊 Cascaded Risks:", {k: f"{v:.1%}" for k,v in propagate_risk(G, services_re).items()})
