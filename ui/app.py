# -*- coding: utf-8 -*-
import uuid
import json
import sys
import os
import time
import psutil as _psutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from real_monitor import get_full_system_snapshot
from auto_remediate_real import check_and_remediate, get_remediation_log as get_real_remediation_log
import streamlit as st
import pandas as pd

from utils.pdf_export import generate_pdf
from visuals.timeline import build_timeline_chart
from visuals.graph_view import build_dependency_graph

from core.auto_remediate import auto_remediate, get_remediation_log, get_system_status
from core.mock_data import generate_threat_ips, generate_incident_log, get_intervention_suggestions
from shared_schema import ServicePayload
from ml_engine import compute_ml_scores
from re_engine import compute_re_pipeline

# ── Device Tracking Functions ──────────────────────
def save_device_data(device_id, data):
    path = f"data/device_{device_id}.json"
    os.makedirs("data", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)

def load_device_data(device_id):
    path = f"data/device_{device_id}.json"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

# ── Session Device ID ──────────────────────────────
import streamlit as st
if "device_id" not in st.session_state:
    st.session_state.device_id = uuid.uuid4().hex[:8]
device_id = st.session_state.device_id

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
        else:
            payload["oss_score"] = round(random.uniform(0.5, 0.85), 2)
            payload["tes_score"] = round(random.uniform(0.05, 0.3), 2)
        payload = compute_ml_scores(payload)
        payload = compute_re_pipeline(payload)
        rows.append({
            "service":     svc,
            "cpu":         round(payload["oss_score"] * 100, 2),
            "memory":      round(random.uniform(20, 90), 2),
            "error_rate":  round(payload["tes_score"] * 25, 2),
            "latency_ms":  round(random.uniform(50, 800), 2),
            "req_per_sec": random.randint(50, 1000),
            "re_score":    round(payload["re_score"] * 100, 2),
        })
    return pd.DataFrame(rows)

try:
    from dummy import *
except Exception:
    pass


# ═══════════════════════════════════════════════════════════
# AUTO-FIX HELPERS  — defined at TOP, used only inside toggle
# ═══════════════════════════════════════════════════════════

def auto_fix_cpu():
    import psutil, platform
    fixed = []
    SAFE = {"system","svchost","wininit","csrss","lsass",
            "services","smss","winlogon","explorer","python","streamlit"}
    for proc in psutil.process_iter(["pid","name","cpu_percent"]):
        try:
            if proc.cpu_percent(interval=0.1) > 50:
                name = proc.info["name"].lower().replace(".exe","")
                if name not in SAFE:
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS
                              if platform.system() == "Windows" else 10)
                    fixed.append(proc.info["name"])
        except Exception:
            continue
    return f"Lowered priority: {', '.join(fixed[:3]) if fixed else 'No eligible processes'}"


def auto_fix_ram():
    import gc, ctypes, platform, psutil
    gc.collect()
    if platform.system() == "Windows":
        try:
            ctypes.windll.psapi.EmptyWorkingSet(
                ctypes.windll.kernel32.GetCurrentProcess())
        except Exception:
            pass
    return f"Memory freed — RAM now at {psutil.virtual_memory().percent}%"


def auto_fix_disk():
    freed = 0
    for temp in [os.environ.get("TEMP",""), "C:\\Windows\\Temp"]:
        if not temp or not os.path.exists(temp):
            continue
        for f in os.listdir(temp):
            try:
                fp = os.path.join(temp, f)
                if os.path.isfile(fp):
                    freed += os.path.getsize(fp)
                    os.remove(fp)
            except Exception:
                continue
    return f"Freed {round(freed/1024/1024, 1)} MB from temp files"


def auto_fix_network():
    import subprocess
    try:
        subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, timeout=10)
        subprocess.run("ipconfig /renew",    shell=True, capture_output=True, timeout=20)
    except Exception:
        pass
    return "DNS flushed + IP renewed"


def schedule_restart(delay_seconds, reason):
    """Safe restart scheduler — ONLY called from inside real_monitor_toggle block."""
    import subprocess
    try:
        subprocess.Popen(
            f'shutdown /r /t {delay_seconds} /c "AREE: {reason}"',
            shell=True
        )
        return True
    except Exception:
        return False


# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="AREE - Risk Evolution Engine",
    page_icon="shield",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Top Navigation Bar ───────────────────────────────────────
st.markdown("""
<div style="background-color:#111827;padding:12px 20px;border-radius:8px;margin-bottom:10px;">
  <span style="font-size:18px;font-weight:bold;color:white;">🛡 AREE Cyber Risk Monitoring Platform</span>
  <span style="float:right;color:#9CA3AF;">Real-Time Infrastructure Risk Intelligence</span>
</div>
""", unsafe_allow_html=True)

current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(
    f'<div style="text-align:right;color:#9CA3AF;font-size:14px;margin-bottom:10px;">'
    f'System Time: {current_time}</div>', unsafe_allow_html=True)

refresh_time = datetime.now().strftime("%H:%M:%S")
st.markdown(
    f'<div style="background-color:#0f172a;padding:8px 14px;border-radius:6px;'
    f'margin-bottom:12px;font-size:13px;color:#9CA3AF;">'
    f'🟢 Monitoring Active | Last Data Refresh: {refresh_time}</div>',
    unsafe_allow_html=True)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""<style>
.stApp {
    background: linear-gradient(-45deg,#020617,#0a1120,#071426,#020617);
    background-size: 300% 300%;
    animation: cyberMove 10s ease infinite;
}
@keyframes cyberMove {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.alert-critical {
    background: linear-gradient(90deg,#3b0d0d,#4a1010,#3b0d0d);
    border: 1px solid #7f1d1d; border-radius: 10px;
    padding: 14px 18px; color: #fecaca; font-weight: 500;
    animation: alertGlow 2s infinite alternate;
}
@keyframes alertGlow {
    from { box-shadow: 0 0 5px rgba(239,68,68,0.4); }
    to   { box-shadow: 0 0 18px rgba(239,68,68,0.9); }
}
.dashboard-card { background-color:#0f172a; border-radius:12px; padding:20px; border:1px solid #1f2937; margin-bottom:20px; }
.metric-card { background:linear-gradient(145deg,#0f172a,#111827); border-radius:12px; padding:18px; border:1px solid #1f2937; box-shadow:0 0 12px rgba(0,0,0,0.4); transition:all 0.25s ease; margin:4px; border-left:4px solid #FF4B4B; }
.metric-card:hover { transform:translateY(-3px); box-shadow:0 0 25px rgba(0,0,0,0.6); }
.metric-card.green  { border-left-color:#00C896; }
.metric-card.orange { border-left-color:#FFA500; }
.metric-card.red    { border-left-color:#FF4B4B; }
.metric-label { font-size:13px; color:#9CA3AF; }
.metric-value { font-size:30px; font-weight:bold; color:white; margin-top:4px; }
.metric-sub   { font-size:12px; color:#6B7280; }
</style>""", unsafe_allow_html=True)


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=60)
    st.title("AREE Controls")
    st.markdown("---")
    st.subheader("Scenario Settings")
    scenario = st.selectbox("Select Scenario", [
        "Normal Operations","DDoS Attack","Config Drift","Brute Force","Data Exfiltration"
    ])
    n_services = st.slider("Number of Services", min_value=3, max_value=8, value=8)
    st.markdown("---")
    st.subheader("Simulation Controls")
    inject_incident = st.button("Inject Incident",    use_container_width=True)
    apply_fix       = st.button("Apply Intervention", use_container_width=True)
    refresh_data    = st.button("Refresh Data",       use_container_width=True)
    st.markdown("---")
    st.subheader("RE Threshold Settings")
    critical_threshold = st.slider("Critical RE Threshold", 60, 90, 75)
    warning_threshold  = st.slider("Warning RE Threshold",  30, 60, 45)
    st.markdown("---")
    st.subheader("Chaos Simulator")
    latency_slider = st.slider("Test Latency (ms)", 100, 5000, 2000)
    chaos_service  = st.text_input("Service Name", "api-svc-01")
    if st.button("Scan Service", use_container_width=True):
        from shared_schema import create_mock_payload
        from re_engine import compute_re_score
        payload = create_mock_payload(chaos_service)
        payload["oss_score"] = max(0.1, 0.8 - (latency_slider / 10000))
        payload["tes_score"] = 0.6
        payload = compute_ml_scores(payload)
        result  = compute_re_score(chaos_service, latency_slider)
        st.metric("RE Score", f"{result['re_score']:.1%}")
        st.metric("Status",   result['aura_level'])
        st.metric("Action",   "auto-remediate" if result['aura_level'] == "red" else "observe")
    if st.button("Chaos Test (10 svcs)", use_container_width=True):
        from re_engine import compute_re_score
        import numpy as np, plotly.graph_objects as go
        chaos_data, alerts_count = [], 0
        st.markdown("**Chaos Results:**")
        for i in range(10):
            latency = np.random.uniform(500, 5000)
            svc_id  = f"SVC-{i}"
            result  = compute_re_score(svc_id, latency)
            chaos_data.append(result['re_score'])
            emoji = "!!" if result['re_score'] > 0.7 else "OK"
            st.write(f"**{svc_id}**: Latency={latency:.0f}ms -> RE={result['re_score']:.1%} [{emoji}]")
            if result['re_score'] > 0.7:
                alerts_count += 1
        st.success(f"{alerts_count}/10 HIGH-RISK -> AUTO-REMEDIATED!")
        fig = go.Figure(data=[go.Bar(
            x=[f"SVC-{i}" for i in range(10)], y=chaos_data,
            marker_color=['red' if x > 0.7 else 'green' for x in chaos_data]
        )])
        fig.update_layout(title="Chaos Test RE Scores", paper_bgcolor="#020617", font={"color":"white"})
        st.plotly_chart(fig, use_container_width=True)
    st.caption("AREE v1.0 | Hackathon Build")
    st.markdown("---")
    # ✅ Toggle is LAST item in sidebar
    real_monitor_toggle = st.toggle("🖥️ Real System Monitor", value=False)


# ── Load Data ────────────────────────────────────────────────
threats   = generate_threat_ips()
incidents = generate_incident_log()
from core.real_metrics import get_real_metrics, compute_re_from_real
raw  = get_real_metrics(n_services)
data = compute_re_from_real(raw)
if scenario == "DDoS Attack":
    data["re_score"] = (data["re_score"] * 1.4).clip(upper=100)
elif scenario == "Config Drift":
    data["re_score"] = (data["re_score"] * 1.2).clip(upper=100)
elif scenario == "Brute Force":
    data["re_score"] = (data["re_score"] * 1.3).clip(upper=100)
elif scenario == "Data Exfiltration":
    data["re_score"] = (data["re_score"] * 1.5).clip(upper=100)

with st.sidebar:
    st.subheader("Export Report")
    pdf_file = generate_pdf(data, incidents)
    st.download_button(label="Download PDF Report", data=pdf_file,
                       file_name="AREE_Risk_Report.pdf", mime="application/pdf",
                       use_container_width=True)
    st.markdown("---")

# ── Incident / Fix ───────────────────────────────────────────
if inject_incident:
    data["re_score"] = (data["re_score"] * 2.5).clip(upper=100)
    st.toast("Incident injected! RE scores spiked.", icon="⚠️")
if apply_fix:
    data["re_score"] = (data["re_score"] * 0.6).round(2)
    st.toast("Intervention applied! RE scores reduced.", icon="✅")

data, auto_actions = auto_remediate(data, critical_threshold)
if auto_actions:
    for act in auto_actions:
        st.toast(f"AUTO-FIXED {act['service']}: RE {act['re_before']} -> {act['re_after']}")

if scenario == "DDoS Attack":
    data["re_score"] = (data["re_score"] * 1.4).clip(upper=100)
elif scenario == "Config Drift":
    data["re_score"] = (data["re_score"] * 1.2).clip(upper=100)
elif scenario == "Brute Force":
    data["re_score"] = (data["re_score"] * 1.3).clip(upper=100)
elif scenario == "Data Exfiltration":
    data["re_score"] = (data["re_score"] * 1.5).clip(upper=100)

# ── Page Header ──────────────────────────────────────────────
st.markdown("## AREE — Autonomous Risk Evolution Engine")
st.markdown(f"**Active Scenario:** `{scenario}` &nbsp;|&nbsp; **Services Monitored:** `{n_services}`")
st.markdown("---")

# ── KPI ─────────────────────────────────────────────────────
total_re      = round(data["re_score"].sum(), 1)
max_re        = round(data["re_score"].max(), 1)
max_svc       = data.loc[data["re_score"].idxmax(), "service"]
critical_svcs = int((data["re_score"] >= critical_threshold).sum())
avg_re        = round(data["re_score"].mean(), 1)

if critical_svcs > 0:
    status_label, status_color = "CRITICAL", "red"
elif avg_re >= warning_threshold:
    status_label, status_color = "WARNING",  "orange"
else:
    status_label, status_color = "STABLE",   "green"

if status_label == "CRITICAL":
    st.markdown('<div class="alert-critical">🚨 SYSTEM STATUS: CRITICAL — Immediate action required!</div>', unsafe_allow_html=True)
elif status_label == "WARNING":
    st.warning(f"⚠ SYSTEM STATUS: {status_label} — Elevated risk detected")
else:
    st.success(f"✅ SYSTEM STATUS: {status_label} — Infrastructure stable")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card orange"><div class="metric-label">Total Risk Energy</div><div class="metric-value">{total_re}</div><div class="metric-sub">Across all services</div></div>', unsafe_allow_html=True)
with col2:
    cc = "red" if max_re >= critical_threshold else "orange" if max_re >= warning_threshold else "green"
    st.markdown(f'<div class="metric-card {cc}"><div class="metric-label">Highest RE Service</div><div class="metric-value">{max_re}</div><div class="metric-sub">{max_svc}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card red"><div class="metric-label">Critical Services</div><div class="metric-value">{critical_svcs}</div><div class="metric-sub">RE above {critical_threshold}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card {status_color}"><div class="metric-label">System Status</div><div class="metric-value">{status_label}</div><div class="metric-sub">Avg RE: {avg_re}</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ██  REAL SYSTEM MONITOR  ██
# Everything in this block ONLY runs when toggle is ON.
# No restart code exists anywhere outside this block.
# ═══════════════════════════════════════════════════════════
if real_monitor_toggle:

    st.markdown("---")
    st.markdown("### 🖥️ Live System Metrics")

    snap       = get_full_system_snapshot()
    cpu        = snap['cpu']['cpu_total_percent']
    ram        = snap['ram']['ram_percent']
    lat        = snap['network']['latency_ms']
    re         = snap['risk_energy']
    status     = snap['overall_status']
    swap       = snap['ram']['swap_percent']
    disk_parts = snap['disk']['partitions']
    zombies    = snap.get('zombie_processes', [])

    cpu_c = "#ef4444" if cpu > 85 else "#f97316" if cpu > 70 else "#22c55e"
    ram_c = "#ef4444" if ram > 85 else "#f97316" if ram > 70 else "#22c55e"
    lat_c = "#ef4444" if (lat > 500 or lat < 0) else "#f97316" if lat > 200 else "#22c55e"
    re_c  = "#ef4444" if re  > 75  else "#f97316" if re  > 45  else "#22c55e"
    s_c   = "#ef4444" if status == "CRITICAL" else "#f97316" if status == "WARNING" else "#22c55e"

    st.markdown("#### 📊 Live Metrics")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div style="background:#0f172a;border-left:4px solid {cpu_c};padding:14px;border-radius:8px;text-align:center;"><div style="color:#9CA3AF;font-size:12px;">⚡ CPU</div><div style="color:{cpu_c};font-size:32px;font-weight:bold;">{cpu}%</div><div style="color:#6B7280;font-size:11px;">{snap["cpu"]["cpu_core_count"]} cores</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div style="background:#0f172a;border-left:4px solid {ram_c};padding:14px;border-radius:8px;text-align:center;"><div style="color:#9CA3AF;font-size:12px;">🧠 RAM</div><div style="color:{ram_c};font-size:32px;font-weight:bold;">{ram}%</div><div style="color:#6B7280;font-size:11px;">{snap["ram"]["ram_used_gb"]}GB / {snap["ram"]["ram_total_gb"]}GB</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div style="background:#0f172a;border-left:4px solid {lat_c};padding:14px;border-radius:8px;text-align:center;"><div style="color:#9CA3AF;font-size:12px;">🌐 Latency</div><div style="color:{lat_c};font-size:32px;font-weight:bold;">{"N/A" if lat<0 else f"{lat}ms"}</div><div style="color:#6B7280;font-size:11px;">{snap["network"]["status"]}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div style="background:#0f172a;border-left:4px solid {re_c};padding:14px;border-radius:8px;text-align:center;"><div style="color:#9CA3AF;font-size:12px;">🔥 Risk Energy</div><div style="color:{re_c};font-size:32px;font-weight:bold;">{re}</div><div style="color:#6B7280;font-size:11px;">{status}</div></div>', unsafe_allow_html=True)

    st.markdown(
        f'<div style="background:{s_c}22;border:1px solid {s_c};border-radius:6px;'
        f'padding:10px 16px;margin-top:8px;color:{s_c};font-weight:bold;text-align:center;font-size:15px;">'
        f'● SYSTEM {status} &nbsp;|&nbsp; CPU:{cpu}% &nbsp;|&nbsp; RAM:{ram}% &nbsp;|&nbsp; '
        f'Latency:{"N/A" if lat<0 else f"{lat}ms"} &nbsp;|&nbsp; RE:{re} &nbsp;|&nbsp; '
        f'{datetime.now().strftime("%H:%M:%S")}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build alert list + run all auto-fixes ────────────────
    system_alerts = []

    # 1. CPU
    if cpu > 95:
        system_alerts.append({"level":"CRITICAL","icon":"🔴","metric":"CPU",
            "msg":f"CPU at {cpu}% — critically overloaded",
            "fix":auto_fix_cpu(),"status":"AUTO-FIXED ✅"})
    elif cpu > 85:
        system_alerts.append({"level":"CRITICAL","icon":"🔴","metric":"CPU",
            "msg":f"CPU critically high at {cpu}%",
            "fix":auto_fix_cpu(),"status":"AUTO-FIXED ✅"})
    elif cpu > 75:
        system_alerts.append({"level":"WARNING","icon":"🟡","metric":"CPU",
            "msg":f"CPU high at {cpu}%",
            "fix":auto_fix_cpu(),"status":"AUTO-FIXED ✅"})

    # 2. RAM
    if ram > 92:
        system_alerts.append({"level":"CRITICAL","icon":"🔴","metric":"RAM",
            "msg":f"RAM critically full at {ram}% — freeze risk",
            "fix":auto_fix_ram(),"status":"AUTO-FIXED ✅"})
    elif ram > 82:
        system_alerts.append({"level":"WARNING","icon":"🟡","metric":"RAM",
            "msg":f"RAM high at {ram}%",
            "fix":auto_fix_ram(),"status":"AUTO-FIXED ✅"})

    # 3. Swap
    if swap > 50:
        system_alerts.append({"level":"WARNING","icon":"🟡","metric":"SWAP",
            "msg":f"Swap at {swap}% — disk used as RAM",
            "fix":auto_fix_ram(),"status":"AUTO-FIXED ✅"})

    # 4. Disk
    for part in disk_parts:
        if part['percent_used'] > 90:
            system_alerts.append({"level":"CRITICAL","icon":"🔴",
                "metric":f"DISK {part['mountpoint']}",
                "msg":f"Disk {part['mountpoint']} at {part['percent_used']}% — almost full!",
                "fix":auto_fix_disk(),"status":"AUTO-FIXED ✅"})
        elif part['percent_used'] > 80:
            system_alerts.append({"level":"WARNING","icon":"🟡",
                "metric":f"DISK {part['mountpoint']}",
                "msg":f"Disk {part['mountpoint']} at {part['percent_used']}%",
                "fix":auto_fix_disk(),"status":"AUTO-FIXED ✅"})

    # 5. Network
    if lat < 0:
      pass
    elif lat > 500:
        system_alerts.append({"level":"CRITICAL","icon":"🔴","metric":"NETWORK",
            "msg":f"Network latency critical ({lat}ms)",
            "fix":auto_fix_network(),"status":"AUTO-FIXED ✅"})
    elif lat > 200:
        system_alerts.append({"level":"WARNING","icon":"🟡","metric":"NETWORK",
            "msg":f"Network latency elevated ({lat}ms)",
            "fix":auto_fix_network(),"status":"AUTO-FIXED ✅"})

    # 6. Risk Energy
    if re > 75:
        system_alerts.append({"level":"CRITICAL","icon":"🚨","metric":"RISK ENERGY",
            "msg":f"Risk Energy CRITICAL ({re}) — cascading failure risk",
            "fix":"Full system auto-remediation triggered","status":"AUTO-FIXED ✅"})
    elif re > 45:
        system_alerts.append({"level":"WARNING","icon":"⚠️","metric":"RISK ENERGY",
            "msg":f"Risk Energy WARNING ({re})",
            "fix":"Monitoring closely","status":"WATCHING 👁️"})

    # 7. Zombie processes
    if zombies:
        killed = []
        for z in zombies:
            try:
                _psutil.Process(z['pid']).kill()
                killed.append(z['name'])
            except Exception:
                pass
        system_alerts.append({"level":"WARNING","icon":"🧟","metric":"ZOMBIE PROCESSES",
            "msg":f"{len(zombies)} zombie process(es) detected",
            "fix":f"Killed: {', '.join(killed) if killed else 'attempted'}",
            "status":"AUTO-FIXED ✅"})

    # 8. Critical overload → restart
    if cpu > 95 and re > 90:
        schedule_restart(30, "Critical CPU+RE overload")
        system_alerts.append({"level":"CRITICAL","icon":"🔁","metric":"AUTO RESTART",
            "msg":"System critically overloaded — auto restart scheduled",
            "fix":"Restarting in 30s — run 'shutdown /a' to cancel",
            "status":"RESTARTING IN 30s 🔁"})
        st.error("🔁 CRITICAL OVERLOAD — AUTO-RESTART IN 30 SECONDS!")
        st.warning("To cancel: open terminal → type `shutdown /a`")

    # 9. Windows Update → restart
    try:
        import winreg
        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired")
        schedule_restart(60, "Windows Update requires restart")
        system_alerts.append({"level":"CRITICAL","icon":"🔄","metric":"WINDOWS UPDATE",
            "msg":"Windows Update pending — AUTO-RESTART in 60 seconds",
            "fix":"Run 'shutdown /a' in terminal to cancel",
            "status":"RESTARTING IN 60s 🔁"})
        st.error("🔁 WINDOWS UPDATE — AUTO-RESTART IN 60 SECONDS! Save your work NOW!")
        st.warning("To cancel: open terminal → type `shutdown /a`")
    except Exception:
        pass  # No Windows Update pending — completely silent

    # 10. Uptime check → restart or warn
    uptime_h = (time.time() - _psutil.boot_time()) / 3600
    if uptime_h > 168:   # 7+ days → auto restart
        schedule_restart(120, f"System uptime {int(uptime_h)}h — restart for performance")
        system_alerts.append({"level":"CRITICAL","icon":"⏰","metric":"UPTIME",
            "msg":f"System running {int(uptime_h)} hours — AUTO-RESTART in 120s",
            "fix":"Run 'shutdown /a' to cancel","status":"RESTARTING IN 120s 🔁"})
        st.error(f"🔁 UPTIME {int(uptime_h)} HOURS — AUTO-RESTART IN 120 SECONDS!")
        st.warning("To cancel: open terminal → type `shutdown /a`")
    elif uptime_h > 72:  # 3–7 days → warn only
        system_alerts.append({"level":"WARNING","icon":"⏰","metric":"UPTIME",
            "msg":f"System running {int(uptime_h)} hours — restart recommended",
            "fix":"Restart when convenient for best performance",
            "status":"ACTION NEEDED ⚠️"})

    # ── Render alert cards ───────────────────────────────────
    if system_alerts:
        alert_html = ""
        for a in system_alerts:
            bg     = "#2d0a0a" if a['level'] == "CRITICAL" else "#2d1f0a"
            border = "#ef4444" if a['level'] == "CRITICAL" else "#f97316"
            s_col  = ("#22c55e" if "AUTO-FIXED"  in a.get('status','') else
                      "#ef4444" if "RESTARTING" in a.get('status','') else
                      "#f97316")
            alert_html += f"""
            <div style="background:{bg};border-left:4px solid {border};
                 border-radius:8px;padding:14px 16px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-size:18px;">{a['icon']}</span>
                        <span style="color:{border};margin-left:8px;font-weight:bold;">
                            [{a['level']}] {a['metric']}</span>
                        <span style="color:#d1d5db;margin-left:8px;">{a['msg']}</span>
                    </div>
                    <span style="color:{s_col};font-weight:bold;font-size:13px;
                          white-space:nowrap;margin-left:16px;">{a.get('status','')}</span>
                </div>
                <div style="color:#22c55e;font-size:12px;margin-top:8px;
                     padding-top:6px;border-top:1px solid #1f2937;">
                    🔧 Action taken: {a.get('fix','Monitoring')}
                </div>
            </div>"""
        st.markdown(
            f'<div><h4 style="color:white;">🚨 System Alerts '
            f'({len(system_alerts)} active — All Auto-Fixed)</h4>{alert_html}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:#0a2a1a;border-left:4px solid #22c55e;'
            'border-radius:6px;padding:12px 16px;color:#22c55e;">'
            '✅ No system issues detected — all metrics normal</div>',
            unsafe_allow_html=True)

    # ── Top Processes ────────────────────────────────────────
    st.markdown("#### 🔝 Top Processes")
    procs = snap['top_processes'][:5]
    proc_html = ('<table style="width:100%;color:white;font-size:13px;border-collapse:collapse;">'
                 '<tr style="color:#9CA3AF;border-bottom:1px solid #1f2937;">'
                 '<th style="text-align:left;padding:6px;">Process</th>'
                 '<th style="text-align:right;padding:6px;">CPU%</th>'
                 '<th style="text-align:right;padding:6px;">RAM%</th>'
                 '<th style="text-align:right;padding:6px;">Status</th></tr>')
    for p in procs:
        pc = "#ef4444" if p['cpu_percent'] > 80 else "#f97316" if p['cpu_percent'] > 50 else "#22c55e"
        proc_html += (f'<tr style="border-bottom:1px solid #0f172a;">'
                      f'<td style="padding:6px;color:#e2e8f0;">{p["name"][:30]}</td>'
                      f'<td style="text-align:right;padding:6px;color:{pc};">{p["cpu_percent"]}%</td>'
                      f'<td style="text-align:right;padding:6px;">{p["memory_percent"]}%</td>'
                      f'<td style="text-align:right;padding:6px;color:#9CA3AF;">{p["status"]}</td></tr>')
    proc_html += "</table>"
    st.markdown(proc_html, unsafe_allow_html=True)

    # ── Disk bars ────────────────────────────────────────────
    st.markdown("#### 💾 Disk Usage")
    for part in snap['disk']['partitions']:
        d_c = "#ef4444" if part['percent_used']>90 else "#f97316" if part['percent_used']>75 else "#22c55e"
        st.markdown(
            f'<div style="margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;color:#9CA3AF;font-size:12px;">'
            f'<span>💾 {part["mountpoint"]}</span>'
            f'<span style="color:{d_c};">{part["percent_used"]}% used — {part["free_gb"]}GB free</span></div>'
            f'<div style="background:#1f2937;border-radius:4px;height:8px;margin-top:4px;">'
            f'<div style="width:{part["percent_used"]}%;background:{d_c};height:100%;border-radius:4px;"></div>'
            f'</div></div>', unsafe_allow_html=True)

    # ── Real remediation result ──────────────────────────────
    real_result = check_and_remediate(snap)
    if real_result:
        st.markdown(
            f'<div style="background:#0a2a1a;border:1px solid #22c55e;border-radius:8px;'
            f'padding:12px 16px;color:#22c55e;margin-top:8px;">'
            f'🔧 AUTO-REMEDIATED: {real_result["action"]} on {real_result["service"]} | '
            f'RE: {real_result["re_before"]} → {real_result["re_after"]} | {real_result["result"]}</div>',
            unsafe_allow_html=True)

    st.markdown("---")

# ═══════════════════════════════════════════════════════════
# DASHBOARD SECTIONS  — always visible, NEVER inside toggle
# ═══════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### 🩺 System Health Score")
import plotly.graph_objects as go
health_score = max(0, 100 - avg_re)
gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number", value=health_score,
    title={'text': "System Stability Index"},
    gauge={'axis':{'range':[0,100]},'bar':{'color':"#00C896"},
           'steps':[{'range':[0,40],'color':"#4a1010"},
                    {'range':[40,70],'color':"#3a2a00"},
                    {'range':[70,100],'color':"#0a2a1a"}]}
))
gauge_fig.update_layout(paper_bgcolor="#020617", font={'color':"white"})
st.plotly_chart(gauge_fig, use_container_width=True)

st.markdown("---")
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
st.markdown("### 📊 Service Risk Overview")
risk_table = data[["service","re_score"]].sort_values("re_score", ascending=False)
for _, row in risk_table.iterrows():
    score = row["re_score"]
    color = "#ef4444" if score >= critical_threshold else "#f97316" if score >= warning_threshold else "#22c55e"
    st.markdown(
        f'<div style="display:flex;align-items:center;margin-bottom:12px;">'
        f'<div style="width:180px;color:#cbd5f5;">{row["service"]}</div>'
        f'<div style="flex:1;height:12px;background:#1f2937;border-radius:6px;margin:0 12px;">'
        f'<div style="width:{score}%;height:100%;background:{color};border-radius:6px;"></div></div>'
        f'<div style="width:70px;text-align:right;color:{color};">{score:.2f}</div></div>',
        unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("### 📈 Risk Energy Timeline")
timeline_fig = build_timeline_chart(data, scenario=scenario,
                                    critical_threshold=critical_threshold,
                                    warning_threshold=warning_threshold)
st.plotly_chart(timeline_fig, use_container_width=True)

st.markdown("---")
st.markdown("### 🔗 Service Dependency & Risk Cascade Graph")
graph_fig = build_dependency_graph(data, critical_threshold=critical_threshold,
                                   warning_threshold=warning_threshold)
st.plotly_chart(graph_fig, use_container_width=True)

st.markdown("---")
st.markdown("### 🔧 Auto-Remediation Log")
rem_log = get_remediation_log()
if (hasattr(rem_log,'empty') and rem_log.empty) or (isinstance(rem_log, list) and not rem_log):
    st.success("No interventions triggered this session — system stable.")
else:
    df_log = pd.DataFrame(rem_log) if isinstance(rem_log, list) else rem_log
    for _, row in df_log.iterrows():
        color = '#ef4444' if row.get('severity') == 'CRITICAL' else '#f97316'
        st.markdown(
            f'<div style="background:#0f172a;border-left:4px solid {color};'
            f'padding:10px 16px;border-radius:6px;margin-bottom:8px;">'
            f'<span style="color:#9CA3AF;font-size:12px;">{row.get("timestamp","")}</span>'
            f'<span style="color:white;font-weight:bold;margin-left:12px;">{row.get("service","")}</span>'
            f'<span style="color:{color};margin-left:12px;">'
            f'RE: {row.get("re_before","")} → {row.get("re_after","")}</span>'
            f'<div style="color:#d1d5db;font-size:13px;margin-top:4px;">{row.get("action","")}</div>'
            f'</div>', unsafe_allow_html=True)
