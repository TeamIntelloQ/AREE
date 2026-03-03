import networkx as nx
import plotly.graph_objects as go
from aree.main_backend import run_aree_pipeline

def build_service_graph():
    G = nx.DiGraph()
    G.add_edges_from([
        ("api-gateway", "payment-service"),
        ("api-gateway", "auth-service"),
        ("auth-service", "db-primary"),
        ("payment-service", "db-primary"),
        ("db-primary", "api-gateway")
    ])
    return G

def viz_risk_graph(re_scores):
    G = build_service_graph()
    pos = {
        "api-gateway": (0, 1),
        "payment-service": (1, 0.5),
        "auth-service": (-1, 0.5),
        "db-primary": (0, 0)
    }
    
    node_sizes = [re_scores.get(node, 20) * 10 for node in G.nodes()]
    node_colors = []
    for node in G.nodes():
        re = re_scores.get(node, 20)
        if re > 70:    color = "#ff4444"
        elif re > 50:  color = "#ff8800"
        else:          color = "#44bb44"
        node_colors.append(color)
    
    edge_weights = []
    for u, v in G.edges():
        re_u = re_scores.get(u, 20)
        weight = min(re_u * 0.1, 20)
        edge_weights.append(weight)
    
    # FIXED: One trace per edge
    edge_traces = []
    for i, (u, v) in enumerate(G.edges()):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            line=dict(width=edge_weights[i], color="#888"),
            hoverinfo='none', mode='lines', showlegend=False
        ))
    
    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>RE: {re_scores.get(node, 0):.1f}")
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text, textposition="middle center",
        marker=dict(size=node_sizes, color=node_colors,
                   line=dict(width=2, color="white"))
    )
    
    fig = go.Figure(data=[*edge_traces, node_trace],
                   layout=go.Layout(
        title="🕸️ Service Risk Network",
        showlegend=False, hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40)
    ))
    fig.update_layout(width=800, height=600)
    return fig

if __name__ == "__main__":
    services_data = {
        "api-gateway":     {"metrics": {"cpu": 0.9, "latency": 500}, "threat": {"ip_score": 0.8}},
        "payment-service": {"metrics": {"cpu": 0.7, "latency": 300}, "threat": {"ip_score": 0.4}},
        "auth-service":    {"metrics": {"cpu": 0.3, "latency": 100}, "threat": {"ip_score": 0.1}},
        "db-primary":      {"metrics": {"cpu": 0.6, "latency": 200}, "threat": {"ip_score": 0.3}}
    }
    result = run_aree_pipeline(services_data)
    fig = viz_risk_graph(result["re_scores"])
    fig.show()
