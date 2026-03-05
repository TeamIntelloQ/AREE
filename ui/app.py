# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import time
from datetime import datetime

from utils.pdf_export import generate_pdf
from visuals.heatmap import build_aura_heatmap
from visuals.timeline import build_timeline_chart
from visuals.graph_view import build_dependency_graph

from core.auto_remediate import auto_remediate, get_remediation_log, get_system_status
from core.mock_data import (
    generate_threat_ips,
    generate_incident_log,
    get_intervention_suggestions
)
from shared_schema import ServicePayload
from ml_engine import compute_ml_scores
from re_engine import compute_re_pipeline

SERVICES = [
    "auth-service", "payment-gateway", "user-db", "api-gateway",
    "notification-svc", "order-service", "inventory-db", "logging-svc",
]

def generate_real_data(n_services, scenario):
    import random
    rows = []
    for svc in SERVICES[:n_services]:
        payload = ServicePayload()
        payload["service_id"] = svc
        # Scenario-based raw inputs
        if scenario == "DDoS Attack":
            payload["oss_score"] = round(random.uniform(0.1, 0.35), 2)
            payload["tes_score"] = round(random.uniform(0.7, 0.95), 2)
        elif scenario == "Config Drift":
            payload["oss_score"] = round(random.uniform(0.3, 0.55), 2)
            payload["tes_score"] = round(random.uniform(0.4, 0.65), 2)
        elif scenario == "Brute Force":
            payload["oss_score"] = round(random.uniform(0.2, 0.5), 2)
            payload["tes_score"] = round(random.uniform(0.75, 0.95), 2)
        elif scenario == "Data Exfiltration":
            payload["oss_score"] = round(random.uniform(0.15, 0.4), 2)
            payload["tes_score"] = round(random.uniform(0.8, 0.99), 2)
        else:  # Normal
            payload["oss_score"] = round(random.uniform(0.5, 0.85), 2)
            payload["tes_score"] = round(random.uniform(0.05, 0.3), 2)

        payload = compute_ml_scores(payload)
        payload = compute_re_pipeline(payload)

        rows.append({
            "service":    svc,
            "cpu":        round(payload["oss_score"] * 100, 2),
            "memory":     round(random.uniform(20, 90), 2),
            "error_rate": round(payload["tes_score"] * 25, 2),
            "latency_ms": round(random.uniform(50, 800), 2),
            "req_per_sec": random.randint(50, 1000),
            "re_score":   round(payload["re_score"] * 100, 2),
        })
    import pandas as pd
    return pd.DataFrame(rows)

# Auto-refresh trigger (Day 2 feature)
try:
    from dummy import *
except:
    pass


# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AREE - Risk Evolution Engine",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ── Top Navigation Bar ───────────────────────────────────────
st.markdown("""
<div style="
    background-color:#111827;
    padding:12px 20px;
    border-radius:8px;
    margin-bottom:10px;
">
<span style="font-size:18px; font-weight:bold; color:white;">
🛡 AREE Cyber Risk Monitoring Platform
</span>

<span style="float:right; color:#9CA3AF;">
Real-Time Infrastructure Risk Intelligence
</span>
</div>
""", unsafe_allow_html=True)


# ── Live System Clock ───────────────────────────────────────
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

st.markdown(
    f"""
    <div style="
        text-align:right;
        color:#9CA3AF;
        font-size:14px;
        margin-bottom:10px;
    ">
    System Time: {current_time}
    </div>
    """,
    unsafe_allow_html=True
)


# ── Live Monitoring Indicator ───────────────────────────────
refresh_time = datetime.now().strftime("%H:%M:%S")

st.markdown(
    f"""
    <div style="
        background-color:#0f172a;
        padding:8px 14px;
        border-radius:6px;
        margin-bottom:12px;
        font-size:13px;
        color:#9CA3AF;
    ">
    🟢 Monitoring Active | Last Data Refresh: {refresh_time}
    </div>
    """,
    unsafe_allow_html=True
)


# ── Custom CSS ─────────────────────────────────────────────
st.markdown("""
<style>
            /* Cyber Grid Background */
.stApp {
    background-color: #020617;
    background-image:
        linear-gradient(rgba(0,255,200,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,200,0.05) 1px, transparent 1px);
    background-size: 40px 40px;
}

/* Subtle glow effect for grid */
.stApp::before{
    content:"";
    position:fixed;
    top:0;
    left:0;
    width:100%;
    height:100%;
    background: radial-gradient(circle at center, rgba(0,255,200,0.08), transparent 70%);
    pointer-events:none;
}
            /* Cyber Alert Banner */
.alert-critical {
    background: linear-gradient(90deg,#3b0d0d,#4a1010,#3b0d0d);
    border: 1px solid #7f1d1d;
    border-radius: 10px;
    padding: 14px 18px;
    color: #fecaca;
    font-weight: 500;
    animation: alertGlow 2s infinite alternate;
}

/* Glow animation */
@keyframes alertGlow {
    from {
        box-shadow: 0 0 5px rgba(239,68,68,0.4);
    }
    to {
        box-shadow: 0 0 18px rgba(239,68,68,0.9);
    }
}
            /* Animated Cyber Background */
/* Animated Cyber Background */
.stApp {
    background: linear-gradient(-45deg,#020617,#0a1120,#071426,#020617);
    background-size: 300% 300%;
    animation: cyberMove 10s ease infinite;
}

/* Animation */
@keyframes cyberMove {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}
/* Dashboard Section Card */
.dashboard-card {
    background-color: #0f172a;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #1f2937;
    margin-bottom: 20px;
}

/* KPI Cards */
.metric-card {
    background: linear-gradient(145deg,#0f172a,#111827);
    border-radius: 12px;
    padding: 18px;
    border: 1px solid #1f2937;
    box-shadow: 0 0 12px rgba(0,0,0,0.4);
    transition: all 0.25s ease;
    margin: 4px;
    border-left: 4px solid #FF4B4B;
}

/* Hover animation */
.metric-card:hover{
    transform: translateY(-3px);
    box-shadow: 0 0 25px rgba(0,0,0,0.6);
}

/* Color indicators */
.metric-card.green  { border-left-color: #00C896; }
.metric-card.orange { border-left-color: #FFA500; }
.metric-card.red    { border-left-color: #FF4B4B; }

/* Text styling */
.metric-label {
    font-size: 13px;
    color: #9CA3AF;
}

.metric-value {
    font-size: 30px;
    font-weight: bold;
    color: white;
    margin-top: 4px;
}

.metric-sub {
    font-size: 12px;
    color: #6B7280;
}

</style>
""", unsafe_allow_html=True)


# ── Sidebar ─────────────────────────────────────────────────
with st.sidebar:

    st.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.title("AREE Controls")

    st.markdown("---")
    st.subheader("Scenario Settings")

    scenario = st.selectbox(
        "Select Scenario",
        ["Normal Operations", "DDoS Attack", "Config Drift", "Brute Force", "Data Exfiltration"]
    )

    n_services = st.slider(
        "Number of Services",
        min_value=3,
        max_value=8,
        value=8
    )

    st.markdown("---")
    st.subheader("Simulation Controls")

    inject_incident = st.button("Inject Incident", use_container_width=True)
    apply_fix = st.button("Apply Intervention", use_container_width=True)
    refresh_data = st.button("Refresh Data", use_container_width=True)

    st.markdown("---")
    st.subheader("RE Threshold Settings")

    critical_threshold = st.slider("Critical RE Threshold", 60, 90, 75)
    warning_threshold = st.slider("Warning RE Threshold", 30, 60, 45)

    st.markdown("---")

    st.markdown("---")
    st.subheader("Chaos Simulator")
    latency_slider = st.slider("Test Latency (ms)", 100, 5000, 2000)
    chaos_service = st.text_input("Service Name", "api-svc-01")

    if st.button("Scan Service", use_container_width=True):
        from shared_schema import create_mock_payload
        from ml_engine import compute_ml_scores
        from re_engine import compute_re_score
        payload = create_mock_payload(chaos_service)
        payload["oss_score"] = max(0.1, 0.8 - (latency_slider / 10000))
        payload["tes_score"] = 0.6
        payload = compute_ml_scores(payload)
        result = compute_re_score(chaos_service, latency_slider)
        st.metric("RE Score", f"{result['re_score']:.1%}")
        st.metric("Status", result['aura_level'])
        st.metric("Action", "auto-remediate" if result['aura_level'] == "red" else "observe")

    if st.button("Chaos Test (10 svcs)", use_container_width=True):
        from re_engine import compute_re_score
        import numpy as np
        chaos_data = []
        alerts = 0
        st.markdown("**Chaos Results:**")
        for i in range(10):
            latency = np.random.uniform(500, 5000)
            svc_id = f"SVC-{i}"
            result = compute_re_score(svc_id, latency)
            chaos_data.append(result['re_score'])
            emoji = "!!" if result['re_score'] > 0.7 else "OK"
            st.write(f"**{svc_id}**: Latency={latency:.0f}ms -> RE={result['re_score']:.1%} [{emoji}]")
            if result['re_score'] > 0.7:
                alerts += 1
        st.success(f"{alerts}/10 HIGH-RISK -> AUTO-REMEDIATED!")
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(
            x=[f"SVC-{i}" for i in range(10)],
            y=chaos_data,
            marker_color=['red' if x > 0.7 else 'green' for x in chaos_data]
        )])
        fig.update_layout(title="Chaos Test RE Scores", paper_bgcolor="#020617", font={"color": "white"})
        st.plotly_chart(fig, use_container_width=True)

    st.caption("AREE v1.0 | Hackathon Build")
    st.markdown("---")


# ── Load Data ───────────────────────────────────────────────
threats = generate_threat_ips()
incidents = generate_incident_log()
from core.real_metrics import get_real_metrics, compute_re_from_real
raw = get_real_metrics(n_services)
data = compute_re_from_real(raw)
if scenario == "DDoS Attack":
    data["re_score"] = (data["re_score"] * 1.4).clip(upper=100)
elif scenario == "Config Drift":
    data["re_score"] = (data["re_score"] * 1.2).clip(upper=100)
elif scenario == "Brute Force":
    data["re_score"] = (data["re_score"] * 1.3).clip(upper=100)
elif scenario == "Data Exfiltration":
    data["re_score"] = (data["re_score"] * 1.5).clip(upper=100)


# ── PDF Export ──────────────────────────────────────────────
with st.sidebar:

    st.subheader("Export Report")

    pdf_file = generate_pdf(data, incidents)

    st.download_button(
        label="Download PDF Report",
        data=pdf_file,
        file_name="AREE_Risk_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.markdown("---")


# ── Auto Remediation ────────────────────────────────────────────
data, auto_actions = auto_remediate(data, critical_threshold)
if auto_actions:
    for act in auto_actions:
        st.toast(f"AUTO-FIXED {act['service']}: RE {act['re_before']} -> {act['re_after']}")

# ── Scenario Modifiers ──────────────────────────────────────
if scenario == "DDoS Attack":
    data["re_score"] = (data["re_score"] * 1.4).clip(upper=100)

elif scenario == "Config Drift":
    data["re_score"] = (data["re_score"] * 1.2).clip(upper=100)

elif scenario == "Brute Force":
    data["re_score"] = (data["re_score"] * 1.3).clip(upper=100)

elif scenario == "Data Exfiltration":
    data["re_score"] = (data["re_score"] * 1.5).clip(upper=100)


if inject_incident:
    data["re_score"] = (data["re_score"] * 1.6).clip(upper=100)
    st.toast("Incident injected! RE scores spiked.", icon="⚠️")

if apply_fix:
    data["re_score"] = (data["re_score"] * 0.6).round(2)
    st.toast("Intervention applied! RE scores reduced.", icon="✅")


# ── Header ──────────────────────────────────────────────────
st.markdown("## AREE — Autonomous Risk Evolution Engine")

st.markdown(
    f"**Active Scenario:** `{scenario}` &nbsp;|&nbsp; **Services Monitored:** `{n_services}`"
)

st.markdown("---")


# ── KPI Calculations ─────────────────────────────────────────
total_re = round(data["re_score"].sum(), 1)
max_re = round(data["re_score"].max(), 1)
max_svc = data.loc[data["re_score"].idxmax(), "service"]
critical_svcs = int((data["re_score"] >= critical_threshold).sum())
avg_re = round(data["re_score"].mean(), 1)

if critical_svcs > 0:
    status_label = "CRITICAL"
    status_color = "red"
elif avg_re >= warning_threshold:
    status_label = "WARNING"
    status_color = "orange"
else:
    status_label = "STABLE"
    status_color = "green"


# ── Status Banner ───────────────────────────────────────────
if status_label == "CRITICAL":
    st.markdown(
        f"""
        <div class="alert-critical">
        🚨 SYSTEM STATUS: {status_label} — Immediate action required!
        </div>
        """,
        unsafe_allow_html=True
    )
elif status_label == "WARNING":
    st.warning(f"⚠ SYSTEM STATUS: {status_label} — Elevated risk detected")
else:
    st.success(f"✅ SYSTEM STATUS: {status_label} — Infrastructure stable")


# ── KPI Cards ───────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card orange">
        <div class="metric-label">Total Risk Energy</div>
        <div class="metric-value">{total_re}</div>
        <div class="metric-sub">Across all services</div>
    </div>
    """, unsafe_allow_html=True)

with col2:

    card_color = (
        "red"
        if max_re >= critical_threshold
        else "orange"
        if max_re >= warning_threshold
        else "green"
    )

    st.markdown(f"""
    <div class="metric-card {card_color}">
        <div class="metric-label">Highest RE Service</div>
        <div class="metric-value">{max_re}</div>
        <div class="metric-sub">{max_svc}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card red">
        <div class="metric-label">Critical Services</div>
        <div class="metric-value">{critical_svcs}</div>
        <div class="metric-sub">RE above {critical_threshold}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card {status_color}">
        <div class="metric-label">System Status</div>
        <div class="metric-value">{status_label}</div>
        <div class="metric-sub">Avg RE: {avg_re}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
# ── System Health Gauge ──────────────────────────────────────
st.markdown("---")
st.markdown("### 🩺 System Health Score")

import plotly.graph_objects as go

health_score = max(0, 100 - avg_re)

gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=health_score,
    title={'text': "System Stability Index"},
    gauge={
        'axis': {'range': [0, 100]},
        'bar': {'color': "#00C896"},
        'steps': [
            {'range': [0, 40], 'color': "#4a1010"},
            {'range': [40, 70], 'color': "#3a2a00"},
            {'range': [70, 100], 'color': "#0a2a1a"}
        ]
    }
))

gauge_fig.update_layout(
    paper_bgcolor="#020617",
    font={'color': "white"}
)

st.plotly_chart(gauge_fig, use_container_width=True)


# ── Service Risk Overview ───────────────────────────────────
st.markdown("---")

st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)

st.markdown("### 📊 Service Risk Overview")

risk_table = data[["service", "re_score"]].sort_values("re_score", ascending=False)

for _, row in risk_table.iterrows():

    score = row["re_score"]

    if score >= critical_threshold:
        color = "#ef4444"   # red
    elif score >= warning_threshold:
        color = "#f97316"   # orange
    else:
        color = "#22c55e"   # green

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; margin-bottom:12px;">

        <div style="width:180px; color:#cbd5f5;">
        {row['service']}
        </div>

        <div style="
        flex:1;
        height:12px;
        background:#1f2937;
        border-radius:6px;
        margin:0 12px;
        ">

        <div style="
        width:{score}%;
        height:100%;
        background:{color};
        border-radius:6px;
        ">
        </div>

        </div>

        <div style="width:70px; text-align:right; color:{color};">
        {score:.2f}
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)
# ── Risk Energy Timeline ─────────────────────────────────────
st.markdown("---")
st.markdown("### 📈 Risk Energy Timeline")

timeline_fig = build_timeline_chart(
    data,
    scenario=scenario,
    critical_threshold=critical_threshold,
    warning_threshold=warning_threshold
)

st.plotly_chart(timeline_fig, use_container_width=True)
# ── Dependency Graph ─────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔗 Service Dependency & Risk Cascade Graph")

graph_fig = build_dependency_graph(
    data,
    critical_threshold=critical_threshold,
    warning_threshold=warning_threshold
)

st.plotly_chart(graph_fig, use_container_width=True)

# ── Auto-Remediation Log ────────────────────────────────────────────
st.markdown('---')
st.markdown('### Auto-Remediation Log')
rem_log = get_remediation_log()
if rem_log.empty:
    st.success('No interventions triggered this session - system stable.')
else:
    for _, row in rem_log.iterrows():
        color = '#ef4444' if row['severity'] == 'CRITICAL' else '#f97316'
        st.markdown(
            f'<div style="background:#0f172a; border-left:4px solid {color}; '
            f'padding:10px 16px; border-radius:6px; margin-bottom:8px;">'
            f'<span style="color:#9CA3AF; font-size:12px;">{row["timestamp"]}</span>'
            f'<span style="color:white; font-weight:bold; margin-left:12px;">{row["service"]}</span>'
            f'<span style="color:{color}; margin-left:12px;">RE: {row["re_before"]} -> {row["re_after"]}</span>'
            f'<div style="color:#d1d5db; font-size:13px; margin-top:4px;">{row["action"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
