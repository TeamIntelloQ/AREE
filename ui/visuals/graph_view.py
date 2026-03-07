# -*- coding: utf-8 -*-
import numpy as np
import networkx as nx
import plotly.graph_objects as go


# Fixed dependency map — which service depends on which
SERVICE_DEPS = {
    "auth-service":      ["api-gateway", "user-db"],
    "payment-gateway":   ["api-gateway", "user-db"],
    "user-db":           [],
    "api-gateway":       [],
    "notification-svc":  ["api-gateway", "auth-service"],
    "order-service":     ["payment-gateway", "inventory-db"],
    "inventory-db":      ["user-db"],
    "logging-svc":       ["api-gateway"],
}


def build_dependency_graph(data_df, critical_threshold=75, warning_threshold=45):
    """
    Builds an interactive NetworkX + Plotly service dependency graph.
    Node size and colour reflect RE severity.
    Edges show risk propagation direction.
    """

    re_map  = dict(zip(data_df["service"].tolist(), data_df["re_score"].tolist()))
    services = data_df["service"].tolist()

    # Build directed graph
    G = nx.DiGraph()
    for svc in services:
        G.add_node(svc, re=re_map.get(svc, 0))

    for svc, deps in SERVICE_DEPS.items():
        if svc in services:
            for dep in deps:
                if dep in services:
                    G.add_edge(svc, dep)

    # Layout — spring layout for organic feel
    np.random.seed(42)
    pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42)

    # ── Edge traces ───────────────────────────────────────────
    edge_traces = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        src_re = re_map.get(edge[0], 0)
        if src_re >= critical_threshold:
            edge_color = "rgba(255,75,75,0.6)"
        elif src_re >= warning_threshold:
            edge_color = "rgba(255,165,0,0.5)"
        else:
            edge_color = "rgba(0,200,150,0.3)"

        edge_traces.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=2, color=edge_color),
            hoverinfo="none",
            showlegend=False
        ))

    # ── Arrow annotations ─────────────────────────────────────
    annotations = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        annotations.append(dict(
            ax=x0, ay=y0,
            x=x1,  y=y1,
            xref="x", yref="y",
            axref="x", ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=1.5,
            arrowcolor="rgba(255,255,255,0.25)"
        ))

    # ── Node trace ────────────────────────────────────────────
    node_x, node_y   = [], []
    node_colors       = []
    node_sizes        = []
    node_texts        = []
    node_hovers       = []

    for svc in G.nodes():
        x, y = pos[svc]
        re   = re_map.get(svc, 0)

        node_x.append(x)
        node_y.append(y)

        # Colour
        if re >= critical_threshold:
            node_colors.append("#FF4B4B")
        elif re >= warning_threshold:
            node_colors.append("#FFA500")
        else:
            node_colors.append("#00C896")

        # Size scales with RE
        node_sizes.append(20 + re * 0.5)

        # Label
        node_texts.append(f"<b>{svc}</b><br>RE: {re:.1f}")

        # Hover
        status = "CRITICAL" if re >= critical_threshold else \
                 "WARNING"  if re >= warning_threshold  else "STABLE"
        deps_out = list(G.successors(svc))
        deps_in  = list(G.predecessors(svc))
        node_hovers.append(
            f"<b>{svc}</b><br>"
            f"RE Score: {re:.1f}<br>"
            f"Status: {status}<br>"
            f"Propagates to: {', '.join(deps_out) if deps_out else 'None'}<br>"
            f"Receives from: {', '.join(deps_in) if deps_in else 'None'}"
        )

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_texts,
        textposition="top center",
        textfont=dict(size=9, color="white"),
        hovertext=node_hovers,
        hoverinfo="text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="rgba(255,255,255,0.3)"),
            opacity=0.9
        ),
        showlegend=False
    )

    # ── Build figure ──────────────────────────────────────────
    fig = go.Figure(
        data=edge_traces + [node_trace],
        layout=go.Layout(
            title=dict(
                text="Service Dependency & Risk Propagation Graph",
                font=dict(size=16, color="white")
            ),
            paper_bgcolor="#0E1117",
            plot_bgcolor="#0E1117",
            font=dict(color="white", family="monospace"),
            xaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False, color="white"),
            yaxis=dict(showgrid=False, zeroline=False,
                       showticklabels=False, color="white"),
            hovermode="closest",
            annotations=annotations,
            height=500,
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False
        )
    )

    return fig
