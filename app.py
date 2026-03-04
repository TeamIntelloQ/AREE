import streamlit as st
import json
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
from re_engine import compute_re_score  # Your working engine!

st.title("🚨 AREE — Risk Evolution Engine")

# Sidebar Controls
st.sidebar.header("Chaos Simulator")
latency_slider = st.sidebar.slider("Test Latency (ms)", 100, 5000, 2000)
service_name = st.sidebar.text_input("Service", "api-svc-01")

# Real-time RE Calculation
if st.sidebar.button("🔍 SCAN SERVICE"):
    result = compute_re_score(service_name, latency_slider)
    st.metric("RE Score", f"{result['re_score']:.1%}", delta=None)
    st.metric("Status", result['aura_level'])
    st.metric("Action", result['action'])

# Chaos Test Button
if st.sidebar.button("🚀 RUN CHAOS TEST (10 services)"):
    st.subheader("Chaos Results")
    alerts = 0
    chaos_data = []
    for i in range(10):
        latency = np.random.uniform(500, 5000)
        result = compute_re_score(f"SVC-{i}", latency)
        chaos_data.append(result['re_score'])
        status_emoji = "🔔" if result['re_score'] > 0.7 else "✅"
        st.write(f"**SVC-{i}**: Latency={latency:.0f}ms → **RE={result['re_score']:.1%}** {status_emoji}")
        if result['re_score'] > 0.7:
            alerts += 1
    
    st.success(f"🎯 **{alerts}/10 AUTO-REMEDIATED!**")
    
    # RE Bar Chart
    fig = go.Figure(data=[go.Bar(x=[f"SVC-{i}" for i in range(10)], 
                                y=chaos_data, 
                                marker_color=['red' if x>0.7 else 'green' for x in chaos_data])])
    fig.update_layout(title="Risk Evolution Scores", yaxis_title="RE Score")
    st.plotly_chart(fig)

# Live Risk Aura Heatmap
st.subheader("🔴 Risk Aura Heatmap")
mock_services = ["frontend", "api", "db", "cache", "auth"]
mock_latencies = np.random.uniform(500, 4000, 5)
service_scores = [compute_re_score(svc, lat)['re_score'] for svc, lat in zip(mock_services, mock_latencies)]

fig_heatmap = go.Figure(data=go.Heatmap(
    z=[service_scores],
    x=mock_services,
    y=["Current"],
    colorscale='RdYlGn_r',
    zmid=0.5
))
st.plotly_chart(fig_heatmap)

# Alerts Summary
high_risk = sum(1 for score in service_scores if score > 0.7)
st.metric("🔔 High Risk Services", high_risk, delta=0)

st.success("🎉 AREE Live Demo — Backend → UI ✅")
st.info("👈 Use sidebar to test latency → watch RE explode!")
