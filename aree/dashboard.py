import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from aree.main_backend import run_aree_pipeline

st.set_page_config(
    page_title="AREE Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AREE — Autonomous Risk Evolution Engine")
st.caption("Real-time Risk Evolution across distributed services")

# ─── Sidebar: Service Config ───────────────────────────
st.sidebar.header("⚙️ Service Inputs")

services_data = {}
service_names = ["api-gateway", "payment-service", "auth-service", "db-primary"]

for svc in service_names:
    st.sidebar.subheader(f"🔹 {svc}")
    cpu     = st.sidebar.slider(f"CPU ({svc})",     0.0, 1.0, 0.5, 0.05)
    latency = st.sidebar.slider(f"Latency ({svc})", 50, 1000, 200, 10)
    ip_score= st.sidebar.slider(f"Threat ({svc})",  0.0, 1.0, 0.3, 0.05)

    services_data[svc] = {
        "metrics": {"cpu": cpu, "latency": latency},
        "threat":  {"ip_score": ip_score}
    }

# ─── Run Pipeline ───────────────────────────────────────
result = run_aree_pipeline(services_data)
re_scores     = result["re_scores"]
forecasts     = result["forecasts"]
interventions = result["interventions"]

# ─── RE Score Cards ─────────────────────────────────────
st.markdown("## 📊 Current Risk Evolution Scores")
cols = st.columns(len(service_names))

for i, svc in enumerate(service_names):
    re = re_scores[svc]
    color = "🔴" if re > 70 else "🟡" if re > 50 else "🟢"
    cols[i].metric(label=f"{color} {svc}", value=f"{re:.2f}", delta=None)

# ─── Risk Aura Heatmap ──────────────────────────────────
st.markdown("## 🌡️ Risk Aura Heatmap")

heatmap_data = pd.DataFrame({
    "Service": list(re_scores.keys()),
    "RE Score": list(re_scores.values())
})

fig_bar = px.bar(
    heatmap_data,
    x="Service",
    y="RE Score",
    color="RE Score",
    color_continuous_scale=["green", "yellow", "red"],
    range_color=[0, 100],
    title="Risk Evolution per Service"
)
fig_bar.add_hline(y=70, line_dash="dash", line_color="red",
                  annotation_text="HIGH threshold")
fig_bar.add_hline(y=50, line_dash="dash", line_color="orange",
                  annotation_text="MEDIUM threshold")
st.plotly_chart(fig_bar, use_container_width=True)

# ─── Forecast Curves ────────────────────────────────────
st.markdown("## 📈 RE Forecasts (Next 10s)")
fig_forecast = go.Figure()

for svc, f in forecasts.items():
    fig_forecast.add_trace(go.Scatter(
        x=f["t"], y=f["re"],
        mode="lines", name=svc
    ))

fig_forecast.add_hline(y=70, line_dash="dot", line_color="red",
                        annotation_text="Intervention threshold")
fig_forecast.update_layout(
    title="Forecasted RE Evolution",
    xaxis_title="Time (s)",
    yaxis_title="RE Score"
)
st.plotly_chart(fig_forecast, use_container_width=True)

# ─── Interventions Table ────────────────────────────────
st.markdown("## 🚨 Recommended Interventions")

if interventions:
   # ✅ FIXED
 df_int = pd.DataFrame(interventions)
 if "re" in df_int.columns:
    df_int = df_int.sort_values("re", ascending=False)
 elif "RE" in df_int.columns:
    df_int = df_int.sort_values("RE", ascending=False)
 st.dataframe(df_int, use_container_width=True)

else:
    st.success("✅ All services nominal — no intervention needed!")

# ─── RL Decisions Table ─────────────────────────────────
st.markdown("## 🤖 RL Agent Decisions")

rl_decisions = result["rl_decisions"]

rl_rows = []
for svc, dec in rl_decisions.items():
    re = re_scores[svc]
    rl_rows.append({
        "Service":  svc,
        "RE Score": round(re, 2),
        "RL Action": dec["action"],
        "Reward":   dec["reward"]
    })

df_rl = pd.DataFrame(rl_rows).sort_values("RE Score", ascending=False)

# Color-code the action column
def color_action(val):
    colors = {
        "SCALE_UP": "background-color: #ff4444; color: white",
        "ISOLATE":  "background-color: #ff8800; color: white",
        "ALERT":    "background-color: #ffcc00; color: black",
        "MONITOR":  "background-color: #44bb44; color: white"
    }
    return colors.get(val, "")

st.dataframe(
    df_rl.style.applymap(color_action, subset=["RL Action"]),
    use_container_width=True
)

# ─── RL Reward Bar ──────────────────────────────────────
fig_reward = px.bar(
    df_rl,
    x="Service",
    y="Reward",
    color="Reward",
    color_continuous_scale=["red", "yellow", "green"],
    title="RL Agent Reward per Service"
)
st.plotly_chart(fig_reward, use_container_width=True)

# ─── Footer ─────────────────────────────────────────────
st.markdown("---")
st.caption("AREE v1.0 | AREE Hackathon 2026 | Built by Khitiz + Team")
