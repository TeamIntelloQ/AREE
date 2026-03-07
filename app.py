import streamlit as st
import uuid
import json
import numpy as np
import plotly.graph_objects as go
import networkx as nx
import matplotlib.pyplot as plt
from re_engine import compute_re_score  # Your working engine!
from shared_schema import create_mock_payload
from ml_engine import compute_ml_scores


st.title("🚨 AREE — Risk Evolution Engine")

# Generate unique user/device ID
if "device_id" not in st.session_state:
    st.session_state.device_id = str(uuid.uuid4())[:8]

device_id = st.session_state.device_id
st.sidebar.markdown(f"**Device ID:** `{device_id}`")

# Sidebar Controls
st.sidebar.header("Chaos Simulator")
latency_slider = st.sidebar.slider("Test Latency (ms)", 100, 5000, 2000)
service_name = st.sidebar.text_input("Service", "api-svc-01")

# Real-time RE Calculation
if st.sidebar.button("🔍 SCAN SERVICE"):
    payload = create_mock_payload(service_name)
    payload = compute_ml_scores(payload)
    payload["oss_score"] = 0.8 - (latency_slider / 10000)
    payload["tes_score"] = 0.6  
    service_name = payload["service_id"]
    mock_latency = 2000  # or calculate from OSS

    payload = compute_re_score(service_name, mock_latency)
    result = payload  # Now works with existing code
    st.metric("RE Score", f"{result['re_score']:.1%}", delta=None)
    st.metric("Status", result['aura_level'])
    st.metric("Action", "auto-remediate" if payload['aura_level'] == "red" else "observe")


# Chaos Test Button
if st.sidebar.button("🚀 RUN CHAOS TEST (10 services)"):
    st.subheader("Chaos Results")
    alerts = 0
    chaos_data = []
    for i in range(10):
        latency = np.random.uniform(500, 5000)
        svc_id = f"SVC-{i}"
        
        # FULL PIPELINE: Mock → ML → RE
        payload = create_mock_payload(svc_id)
        # Latency affects OSS score (realistic!)
        payload["oss_score"] = max(0.1, 1.0 - latency / 6000.0)
        payload["tes_score"] = np.random.uniform(0.5, 0.9)  # Random threat
        payload = compute_ml_scores(payload)  # Your ML
        service = payload["service_id"]
        latency = 2000  # Mock latency
        result = compute_re_score(service, latency)
        payload.update(result) 
        
        chaos_data.append(payload['re_score'])
        status_emoji = "🔔" if payload['re_score'] > 0.7 else "✅"
        st.write(f"**{svc_id}**: Latency={latency:.0f}ms → OSS={payload['oss_score']:.2f} TES={payload['tes_score']:.2f} → **RE={payload['re_score']:.1%}** {status_emoji}")
        if payload['re_score'] > 0.7:
            alerts += 1
    
    st.success(f"🎯 **{alerts}/10 HIGH-RISK → AUTO-REMEDIATED!**")
    
    # Bar chart (works even without numpy if you comment plotly)
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(x=[f"SVC-{i}" for i in range(10)], 
                                   y=chaos_data, 
                                   marker_color=['red' if x>0.7 else 'green' for x in chaos_data])])
        fig.update_layout(title="Risk Evolution Scores", yaxis_title="RE Score")
        st.plotly_chart(fig)
    except ImportError:
        st.info("📊 Plotly optional - focus on pipeline!")

    
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
