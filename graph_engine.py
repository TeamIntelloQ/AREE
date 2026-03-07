import networkx as nx
from graph_engine import build_service_graph, compute_dss_graph
def build_service_graph():
    G = nx.DiGraph()

    services = [
        "api-gateway", "auth-service", "payment-service",
        "db-primary", "db-replica", "redis-cache",
        "notification-service", "ml-model-service"
    ]

    G.add_nodes_from(services)

    G.add_edges_from([
        ("api-gateway", "auth-service"),
        ("api-gateway", "payment-service"),
        ("payment-service", "db-primary"),
        ("db-primary", "db-replica"),
        ("auth-service", "redis-cache"),
        ("payment-service", "notification-service"),
        ("ml-model-service", "api-gateway"),
        ("db-primary", "redis-cache"),
    ])

    return G

def compute_dss_graph(G, service_re_map, node, depth=0, max_depth=3, decay=0.8):
    if depth >= max_depth:
        return 0.0
    children = list(G.successors(node))
    if not children:
        return 0.0
    child_scores = []
    for child in children:
        child_re = service_re_map.get(child, 0)
        propagated = child_re * (decay ** depth)
        child_scores.append(
            propagated + compute_dss_graph(
                G, service_re_map, child,
                depth+1, max_depth, decay
            )
        )
    return round(sum(child_scores) / len(child_scores) / 100, 4)

if __name__ == "__main__":
    G = build_service_graph()
    mock_re_map = {
        "payment-service": 80,
        "db-primary": 65,
        "db-replica": 40,
        "auth-service": 30,
        "redis-cache": 20,
        "notification-service": 50,
        "api-gateway": 45,
        "ml-model-service": 35
    }
    dss = compute_dss_graph(G, mock_re_map, "api-gateway")
    print("=" * 40)
    print(f"  Nodes : {list(G.nodes)}")
    print(f"  Edges : {list(G.edges)}")
    print(f"  DSS for api-gateway: {dss}")
    print("=" * 40)
