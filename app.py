from services.forecast import forecast_re  # ADD THIS
import streamlit as st
import json
import networkx as nx
import plotly.graph_objects as go
from services.alerts import monitor_ip
from services.graph_prop import propagate_risk  # Update import if needed

st.title("🚨 AREE — Risk Evolution Engine")

# Load data
events = json.load(open('data/sample_events.json'))
services_re = {e['service']: monitor_ip(e['ip'], e['oss'], e['sts'], e['bcs'])/100 
               for e in events}

# Metrics
st.metric("Max RE", f"{max(services_re.values()):.1%}")
st.metric("Alerts", len([v for v in services_re.values() if v > 0.75]))

# RE Bar Chart
st.subheader("RE Scores")
fig = go.Figure(data=[go.Bar(x=list(services_re.keys()), 
                            y=list(services_re.values()))])
st.plotly_chart(fig)
# ADD THIS ENTIRE BLOCK:
st.subheader("🔮 RE Forecast")
re_history = list(services_re.values())[:5]  # Last 5 services
future_re = forecast_re(re_history)

st.line_chart(future_re)

max_future = max(future_re)
if max_future > 0.75:
    st.error(f"🚨 CRITICAL: Spike to {max_future:.1%} predicted!")
else:
    st.info("✅ Trajectory stable")

# Risk Graph
st.subheader("Propagation Graph")
G = nx.DiGraph([("frontend","api"),("api","db")])
risk_map = propagate_risk(G, services_re)
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color=list(risk_map.values()), 
        node_size=[v*5000 for v in risk_map.values()])
st.pyplot()

st.success("🎉 Backend → UI Complete!")
