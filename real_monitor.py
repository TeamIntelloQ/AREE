"""
AREE — Real System Monitor
Works correctly on BOTH localhost and Streamlit Cloud.
On Streamlit Cloud: uses JavaScript to get client browser stats.
On localhost: uses psutil for full accurate metrics.
"""

import psutil
import time
import platform
import subprocess
import requests
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components


# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
MONITOR_CONFIG = {
    "poll_interval_seconds": 5,
    "network_interface": None,
    "high_cpu_threshold": 85,
    "high_ram_threshold": 85,
    "high_disk_threshold": 90,
    "latency_test_host": "8.8.8.8",
    "top_processes_count": 10,
}


# ─────────────────────────────────────────
# DETECT ENVIRONMENT
# ─────────────────────────────────────────
def is_streamlit_cloud() -> bool:
    """Detects if running on Streamlit Cloud vs localhost."""
    import os
    return (
        os.environ.get("STREAMLIT_SHARING_MODE") == "streamlit_sharing" or
        os.environ.get("HOME") == "/home/appuser" or
        os.path.exists("/mount/src")
    )


# ─────────────────────────────────────────
# 1. CPU MONITORING
# ─────────────────────────────────────────
def get_cpu_metrics() -> dict:
    """Returns CPU metrics — accurate single reading."""
    cpu_total = psutil.cpu_percent(interval=1)
    cpu_percent_per_core = psutil.cpu_percent(interval=None, percpu=True)
    cpu_freq = psutil.cpu_freq()
    load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)

    # On Streamlit Cloud: override core count with client's actual cores
    core_count = psutil.cpu_count(logical=True)
    if is_streamlit_cloud() and "client_cores" in st.session_state:
        core_count = st.session_state["client_cores"]

    return {
        "cpu_total_percent":  cpu_total,
        "cpu_per_core":       cpu_percent_per_core,
        "cpu_core_count":     core_count,
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_freq_mhz":       round(cpu_freq.current, 1) if cpu_freq else 0,
        "cpu_freq_max_mhz":   round(cpu_freq.max, 1) if cpu_freq else 0,
        "load_avg_1min":      round(load_avg[0], 2),
        "load_avg_5min":      round(load_avg[1], 2),
        "load_avg_15min":     round(load_avg[2], 2),
        "status": "CRITICAL" if cpu_total > MONITOR_CONFIG["high_cpu_threshold"]
                  else "WARNING" if cpu_total > 70
                  else "NORMAL",
    }


# ─────────────────────────────────────────
# 2. RAM MONITORING
# ─────────────────────────────────────────
def get_ram_metrics() -> dict:
    """Returns RAM metrics. On cloud, uses client-reported RAM if available."""
    ram  = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # On Streamlit Cloud: use client device RAM from JS injection
    if is_streamlit_cloud() and "client_ram_total_gb" in st.session_state:
        total_gb = st.session_state["client_ram_total_gb"]
        percent  = st.session_state.get("client_ram_percent", ram.percent)
        used_gb  = round(total_gb * (percent / 100), 2)
    else:
        total_gb = round(ram.total / (1024**3), 2)
        used_gb  = round(ram.used  / (1024**3), 2)
        percent  = ram.percent

    return {
        "ram_total_gb":     total_gb,
        "ram_used_gb":      used_gb,
        "ram_available_gb": round(ram.available / (1024**3), 2),
        "ram_percent":      percent,
        "ram_cached_gb":    round(getattr(ram, "cached", 0) / (1024**3), 2),
        "swap_total_gb":    round(swap.total / (1024**3), 2),
        "swap_used_gb":     round(swap.used  / (1024**3), 2),
        "swap_percent":     swap.percent,
        "status": "CRITICAL" if percent > MONITOR_CONFIG["high_ram_threshold"]
                  else "WARNING" if percent > 70
                  else "NORMAL",
    }


# ─────────────────────────────────────────
# 3. DISK MONITORING
# ─────────────────────────────────────────
def get_disk_metrics() -> dict:
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device":       part.device,
                "mountpoint":   part.mountpoint,
                "fstype":       part.fstype,
                "total_gb":     round(usage.total / (1024**3), 2),
                "used_gb":      round(usage.used  / (1024**3), 2),
                "free_gb":      round(usage.free  / (1024**3), 2),
                "percent_used": usage.percent,
                "status": "CRITICAL" if usage.percent > MONITOR_CONFIG["high_disk_threshold"]
                          else "WARNING" if usage.percent > 75
                          else "NORMAL",
            })
        except PermissionError:
            continue

    disk_io = psutil.disk_io_counters()
    io_metrics = {}
    if disk_io:
        io_metrics = {
            "read_mb":    round(disk_io.read_bytes  / (1024**2), 2),
            "write_mb":   round(disk_io.write_bytes / (1024**2), 2),
            "read_count":  disk_io.read_count,
            "write_count": disk_io.write_count,
        }

    return {
        "partitions": partitions,
        "io": io_metrics,
        "overall_status": "CRITICAL" if any(p["status"] == "CRITICAL" for p in partitions)
                          else "WARNING" if any(p["status"] == "WARNING" for p in partitions)
                          else "NORMAL",
    }


# ─────────────────────────────────────────
# 4. NETWORK MONITORING
# ─────────────────────────────────────────
def get_network_latency_ms(host: str = "8.8.8.8") -> float:
    """HTTP latency with multiple fallbacks."""
    for url in ["https://www.google.com", "https://www.cloudflare.com", "https://one.one.one.one"]:
        try:
            r = requests.get(url, timeout=3)
            return round(r.elapsed.total_seconds() * 1000, 1)
        except Exception:
            continue
    try:
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", host]
        else:
            cmd = ["ping", "-c", "1", "-W", "2", host]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        output = result.stdout
        if platform.system().lower() == "windows":
            for line in output.splitlines():
                if "Average" in line:
                    parts = line.split("=")
                    if len(parts) > 1:
                        return float(parts[-1].replace("ms", "").strip())
        else:
            for line in output.splitlines():
                if "avg" in line or "rtt" in line:
                    parts = line.split("/")
                    if len(parts) >= 5:
                        return float(parts[4])
    except Exception:
        pass
    return -1.0


def get_network_metrics() -> dict:
    net_io = psutil.net_io_counters()
    interfaces = {}
    for name, stats in psutil.net_if_stats().items():
        addrs = psutil.net_if_addrs().get(name, [])
        ip = next((a.address for a in addrs if a.family.name == "AF_INET"), "N/A")
        interfaces[name] = {
            "is_up":      stats.isup,
            "speed_mbps": stats.speed,
            "mtu":        stats.mtu,
            "ip_address": ip,
        }
    latency = get_network_latency_ms(MONITOR_CONFIG["latency_test_host"])
    return {
        "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
        "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
        "packets_sent":  net_io.packets_sent,
        "packets_recv":  net_io.packets_recv,
        "errors_in":     net_io.errin,
        "errors_out":    net_io.errout,
        "dropped_in":    net_io.dropin,
        "dropped_out":   net_io.dropout,
        "latency_ms":    latency,
        "interfaces":    interfaces,
        "status": "CRITICAL" if latency < 0 or latency > 500
                  else "WARNING" if latency > 150
                  else "NORMAL",
    }


# ─────────────────────────────────────────
# 5. PROCESS MONITORING
# ─────────────────────────────────────────
def get_top_processes(n: int = 10) -> list:
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent",
                                      "memory_percent", "status", "username"]):
        try:
            info = proc.info
            if info["cpu_percent"] is not None:
                procs.append({
                    "pid":            info["pid"],
                    "name":           info["name"],
                    "cpu_percent":    round(info["cpu_percent"], 2),
                    "memory_percent": round(info["memory_percent"] or 0, 2),
                    "status":         info["status"],
                    "user":           info["username"] or "N/A",
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:n]


def get_zombie_processes() -> list:
    zombies = []
    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                zombies.append({
                    "pid":    proc.info["pid"],
                    "name":   proc.info["name"],
                    "status": "ZOMBIE",
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return zombies


# ─────────────────────────────────────────
# 6. FULL SYSTEM SNAPSHOT
# ─────────────────────────────────────────
def get_full_system_snapshot() -> dict:
    snapshot = {
        "timestamp":        datetime.now().isoformat(),
        "hostname":         platform.node(),
        "os":               f"{platform.system()} {platform.release()}",
        "cpu":              get_cpu_metrics(),
        "ram":              get_ram_metrics(),
        "disk":             get_disk_metrics(),
        "network":          get_network_metrics(),
        "top_processes":    get_top_processes(MONITOR_CONFIG["top_processes_count"]),
        "zombie_processes": get_zombie_processes(),
    }
    snapshot["risk_energy"]    = compute_system_re(snapshot)
    snapshot["overall_status"] = (
        "CRITICAL" if snapshot["risk_energy"] > 75
        else "WARNING" if snapshot["risk_energy"] > 45
        else "STABLE"
    )
    return snapshot


# ─────────────────────────────────────────
# 7. RISK ENERGY CALCULATION
# ─────────────────────────────────────────
def compute_system_re(snapshot: dict) -> float:
    cpu_score  = snapshot["cpu"]["cpu_total_percent"]
    ram_score  = snapshot["ram"]["ram_percent"]
    disk_parts = snapshot["disk"]["partitions"]
    disk_score = max((p["percent_used"] for p in disk_parts), default=0)
    latency    = snapshot["network"]["latency_ms"]
    net_score  = 50 if latency < 0 else min(100, (latency / 1000) * 100)
    re = (
        cpu_score  * 0.35 +
        ram_score  * 0.30 +
        disk_score * 0.15 +
        net_score  * 0.20
    )
    return round(re, 2)


# ─────────────────────────────────────────
# 8. STREAMLIT CLOUD CLIENT STATS INJECTOR
# ─────────────────────────────────────────
def inject_client_stats():
    """
    Call this ONCE at the top of your real_monitor_toggle block.
    On Streamlit Cloud: reads client device RAM/cores via JS
    and stores in session_state so psutil values get overridden.
    On localhost: does nothing (psutil is already accurate).
    """
    if not is_streamlit_cloud():
        return

    # Inject JS to read client device memory and cores
    components.html("""
    <script>
    (function() {
        var deviceRamGB = navigator.deviceMemory || null;
        var cores = navigator.hardwareConcurrency || null;
        if (deviceRamGB || cores) {
            var url = new URL(window.parent.location.href);
            if (deviceRamGB) url.searchParams.set('client_ram_gb', deviceRamGB);
            if (cores)       url.searchParams.set('client_cores',  cores);
            window.parent.history.replaceState({}, '', url.toString());
            window.parent.location.reload();
        }
    })();
    </script>
    """, height=0)

    # Read injected values from query params
    params = st.query_params
    if "client_ram_gb" in params:
        try:
            ram_gb = float(params["client_ram_gb"])
            st.session_state["client_ram_total_gb"] = ram_gb
            st.session_state["client_ram_percent"]  = psutil.virtual_memory().percent
        except Exception:
            pass
    if "client_cores" in params:
        try:
            st.session_state["client_cores"] = int(params["client_cores"])
        except Exception:
            pass


# ─────────────────────────────────────────
# 9. CONTINUOUS MONITORING LOOP
# ─────────────────────────────────────────
def start_monitoring_loop(callback=None, stop_event=None):
    print(f"[AREE Monitor] Started — polling every {MONITOR_CONFIG['poll_interval_seconds']}s")
    while True:
        if stop_event and stop_event.is_set():
            print("[AREE Monitor] Stopped.")
            break
        snapshot = get_full_system_snapshot()
        if callback:
            callback(snapshot)
        else:
            print(
                f"[{snapshot['timestamp']}] "
                f"CPU={snapshot['cpu']['cpu_total_percent']}% | "
                f"RAM={snapshot['ram']['ram_percent']}% | "
                f"Latency={snapshot['network']['latency_ms']}ms | "
                f"RE={snapshot['risk_energy']} → {snapshot['overall_status']}"
            )
        time.sleep(MONITOR_CONFIG["poll_interval_seconds"])


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("AREE Real System Monitor — Live Snapshot")
    print("=" * 60)
    snap = get_full_system_snapshot()
    print(f"\n🖥  Host      : {snap['hostname']} ({snap['os']})")
    print(f"🕐  Time      : {snap['timestamp']}")
    print(f"\n⚡  CPU       : {snap['cpu']['cpu_total_percent']}% ({snap['cpu']['cpu_core_count']} cores)")
    print(f"🧠  RAM       : {snap['ram']['ram_used_gb']}GB / {snap['ram']['ram_total_gb']}GB ({snap['ram']['ram_percent']}%)")
    print(f"💾  Disk      : {snap['disk']['overall_status']}")
    for p in snap['disk']['partitions']:
        print(f"     {p['mountpoint']} → {p['percent_used']}% used ({p['free_gb']}GB free)")
    print(f"🌐  Latency   : {snap['network']['latency_ms']}ms | {snap['network']['status']}")
    print(f"\n🔥  RE Score  : {snap['risk_energy']} → {snap['overall_status']}")
    print(f"\n🔝 Top Processes:")
    for proc in snap['top_processes'][:5]:
        print(f"    {proc['name']:25s} CPU={proc['cpu_percent']}%  RAM={proc['memory_percent']}%")
