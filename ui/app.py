# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from visuals.heatmap import build_aura_heatmap
from visuals.timeline import build_timeline_chart
from visuals.graph_view import build_dependency_graph



from core.mock_data import (
    generate_service_metrics,
    generate_threat_ips,
    generate_incident_log,
    compute_re_scores,
    get_intervention_suggestions
)

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="AREE - Risk Evolution Engine",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS for coloured metric cards ─────────────────────
st.markdown("""
<style>
.metric-card {
    background-color: #1A1E2E;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 4px;
    border-left: 4px solid #FF4B4B;
}
.metric-card.green  { border-left-color: #00C896; }
.metric-card.orange { border-left-color: #FFA500; }
.metric-card.red    { border-left-color: #FF4B4B; }
.metric-label {
    font-size: 13px;
    color: #AAAAAA;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: #FFFFFF;
}
.metric-sub {
    font-size: 12px;
    color: #888888;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.title("AREE Controls")
    st.markdown("---")

    st.subheader("Scenario Settings")
    scenario = st.selectbox(
        "Select Scenario",
        ["Normal Operations", "DDoS Attack", "Config Drift", "Brute Force", "Data Exfiltration"]
    )

    n_services = st.slider("Number of Services", min_value=3, max_value=8, value=8)

    st.markdown("---")
    st.subheader("Simulation Controls")

    inject_incident = st.button("Inject Incident", use_container_width=True)
    apply_fix       = st.button("Apply Intervention", use_container_width=True)
    refresh_data    = st.button("Refresh Data", use_container_width=True)

    st.markdown("---")
    st.subheader("RE Threshold Settings")
    critical_threshold = st.slider("Critical RE Threshold", 60, 90, 75)
    warning_threshold  = st.slider("Warning RE Threshold",  30, 60, 45)

    st.markdown("---")
    st.caption("AREE v1.0 | Hackathon Build")


# ── Load Data ─────────────────────────────────────────────────
metrics   = generate_service_metrics(n_services)
threats   = generate_threat_ips()
incidents = generate_incident_log()
data      = compute_re_scores(metrics, threats)

# Scenario modifier — spikes RE on attack scenarios
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


# ── Header ────────────────────────────────────────────────────
st.markdown("## AREE — Autonomous Risk Evolution Engine")
st.markdown(f"**Active Scenario:** `{scenario}` &nbsp;|&nbsp; **Services Monitored:** `{n_services}`")
st.markdown("---")


# ── KPI Cards ─────────────────────────────────────────────────
total_re      = round(data["re_score"].sum(), 1)
max_re        = round(data["re_score"].max(), 1)
max_svc       = data.loc[data["re_score"].idxmax(), "service"]
critical_svcs = int((data["re_score"] >= critical_threshold).sum())
avg_re        = round(data["re_score"].mean(), 1)

# Determine system status
if critical_svcs > 0:
    status_label = "CRITICAL"
    status_color = "red"
elif avg_re >= warning_threshold:
    status_label = "WARNING"
    status_color = "orange"
else:
    status_label = "STABLE"
    status_color = "green"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card orange">
        <div class="metric-label">Total Risk Energy</div>
        <div class="metric-value">{total_re}</div>
        <div class="metric-sub">Across all services</div>
    </div>""", unsafe_allow_html=True)

with col2:
    card_color = "red" if max_re >= critical_threshold else "orange" if max_re >= warning_threshold else "green"
    st.markdown(f"""
    <div class="metric-card {card_color}">
        <div class="metric-label">Highest RE Service</div>
        <div class="metric-value">{max_re}</div>
        <div class="metric-sub">{max_svc}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card red">
        <div class="metric-label">Critical Services</div>
        <div class="metric-value">{critical_svcs}</div>
        <div class="metric-sub">RE above {critical_threshold}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card {status_color}">
        <div class="metric-label">System Status</div>
        <div class="metric-value">{status_label}</div>
        <div class="metric-sub">Avg RE: {avg_re}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Service Table ─────────────────────────────────────────────
st.markdown("### Service Risk Overview")
# ── Risk Aura Heatmap ─────────────────────────────────────────
st.markdown("---")
st.markdown("### Risk Aura Visualization")
st.caption("Live risk energy field — colour intensity reflects RE severity per service")

fig = build_aura_heatmap(data, critical_threshold, warning_threshold)
st.pyplot(fig)
# ── RE Timeline Chart ─────────────────────────────────────────
st.markdown("---")
st.markdown("### Risk Energy Timeline")
st.caption("Historical RE evolution per service + dotted forecast zone")

timeline_fig = build_timeline_chart(
    data,
    scenario=scenario,
    critical_threshold=critical_threshold,
    warning_threshold=warning_threshold
)
st.plotly_chart(timeline_fig, use_container_width=True)
# ── Dependency Graph ──────────────────────────────────────────
st.markdown("---")
st.markdown("### Service Dependency & Risk Cascade Graph")
st.caption("Node size = RE magnitude | Colour = severity | Arrows = risk propagation direction")

graph_fig = build_dependency_graph(
    data,
    critical_threshold=critical_threshold,
    warning_threshold=warning_threshold
)
st.plotly_chart(graph_fig, use_container_width=True)
# ── What-If Simulation Panel ──────────────────────────────────
st.markdown("---")
st.markdown("### What-If Simulation Panel")
st.caption("Simulate targeted attacks on specific services and observe cascade impact")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("#### Configure Simulation")

    target_svc = st.selectbox(
        "Target Service",
        options=data["service"].tolist(),
        key="whatif_svc"
    )

    attack_type = st.selectbox(
        "Attack Type",
        ["DDoS Flood", "Memory Exhaustion", "CPU Spike",
         "Auth Bypass", "Data Exfil Attempt"],
        key="whatif_attack"
    )

    attack_intensity = st.slider(
        "Attack Intensity", 1, 10, 5,
        key="whatif_intensity"
    )

    run_sim = st.button("Run What-If Simulation", use_container_width=True)

with col_right:
    st.markdown("#### Simulation Result")

    if run_sim:
        # Apply attack to target service
        sim_data = data.copy()
        boost    = attack_intensity * 4.5
        mask     = sim_data["service"] == target_svc
        sim_data.loc[mask, "re_score"] = (
            sim_data.loc[mask, "re_score"] + boost
        ).clip(upper=100)

        # Cascade to dependencies
        from visuals.graph_view import SERVICE_DEPS
        cascade_svcs = SERVICE_DEPS.get(target_svc, [])
        for dep in cascade_svcs:
            dep_mask = sim_data["service"] == dep
            if dep_mask.any():
                sim_data.loc[dep_mask, "re_score"] = (
                    sim_data.loc[dep_mask, "re_score"] + boost * 0.4
                ).clip(upper=100)

        new_re   = sim_data.loc[sim_data["service"] == target_svc, "re_score"].values[0]
        delta_re = new_re - data.loc[data["service"] == target_svc, "re_score"].values[0]

        st.error(f"ATTACK SIMULATED: {attack_type} on {target_svc}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Target RE",    f"{new_re:.1f}",   delta=f"+{delta_re:.1f}")
        m2.metric("Cascades Hit", f"{len(cascade_svcs)}", delta="services affected")
        m3.metric("Intensity",    f"{attack_intensity}/10")

        if cascade_svcs:
            st.warning(f"Cascade propagation detected → {', '.join(cascade_svcs)}")
        else:
            st.info("No downstream cascades detected for this service.")

        st.markdown("**Post-Attack RE Overview:**")
        st.dataframe(
            sim_data[["service", "re_score"]].style.applymap(
                lambda v: "background-color:#4a1010;color:#FF6B6B"
                if v >= critical_threshold
                else "background-color:#3a2a00;color:#FFA500"
                if v >= warning_threshold
                else "background-color:#0a2a1a;color:#00C896",
                subset=["re_score"]
            ),
            use_container_width=True
        )
    else:
        st.info("Configure an attack above and click 'Run What-If Simulation' to see cascade impact.")


# ── Intervention Suggestions ──────────────────────────────────
st.markdown("---")
st.markdown("### AREE Intervention Recommendations")
st.caption("Autonomous suggestions based on current RE levels")

suggestions = get_intervention_suggestions(data, critical_threshold, warning_threshold)

if not suggestions.empty:
    for _, row in suggestions.iterrows():
        if row["status"] == "CRITICAL":
            st.error(
                f"**CRITICAL — {row['service']}** (RE: {row['re_score']:.1f})  \n"
                f"Action: {row['action']}  \n"
                f"{row['suggestion']}"
            )
        else:
            st.warning(
                f"**WARNING — {row['service']}** (RE: {row['re_score']:.1f})  \n"
                f"Action: {row['action']}  \n"
                f"{row['suggestion']}"
            )
else:
    st.success("All services stable. No interventions required.")


# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#555; font-size:12px;'>"
    "AREE — Autonomous Risk Evolution Engine | Hackathon Build 2026 | "
    "Powered by Physics-Inspired Risk Simulation"
    "</div>",
    unsafe_allow_html=True
)


