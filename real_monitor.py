"""
AREE — Real System Monitor
Tracks: CPU, RAM, Disk, Network, Processes
Works on: Windows, Linux, MacOS
Install: pip install psutil requests
"""

import psutil
import time
import platform
import subprocess
import requests
from datetime import datetime


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
# 1. CPU MONITORING
# ─────────────────────────────────────────
def get_cpu_metrics() -> dict:
    """Returns detailed CPU usage metrics — single accurate reading."""
    # ONE call with interval — this is the accurate reading, reused everywhere
    cpu_total = psutil.cpu_percent(interval=1)
    cpu_percent_per_core = psutil.cpu_percent(interval=None, percpu=True)
    cpu_freq = psutil.cpu_freq()
    load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)

    return {
        "cpu_total_percent": cpu_total,
        "cpu_per_core": cpu_percent_per_core,
        "cpu_core_count": psutil.cpu_count(logical=True),
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_freq_mhz": round(cpu_freq.current, 1) if cpu_freq else 0,
        "cpu_freq_max_mhz": round(cpu_freq.max, 1) if cpu_freq else 0,
        "load_avg_1min": round(load_avg[0], 2),
        "load_avg_5min": round(load_avg[1], 2),
        "load_avg_15min": round(load_avg[2], 2),
        "status": "CRITICAL" if cpu_total > MONITOR_CONFIG["high_cpu_threshold"]
                  else "WARNING" if cpu_total > 70
                  else "NORMAL",
    }


# ─────────────────────────────────────────
# 2. RAM MONITORING
# ─────────────────────────────────────────
def get_ram_metrics() -> dict:
    """Returns RAM and swap memory metrics."""
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "ram_total_gb": round(ram.total / (1024 ** 3), 2),
        "ram_used_gb": round(ram.used / (1024 ** 3), 2),
        "ram_available_gb": round(ram.available / (1024 ** 3), 2),
        "ram_percent": ram.percent,
        "ram_cached_gb": round(getattr(ram, "cached", 0) / (1024 ** 3), 2),
        "swap_total_gb": round(swap.total / (1024 ** 3), 2),
        "swap_used_gb": round(swap.used / (1024 ** 3), 2),
        "swap_percent": swap.percent,
        "status": "CRITICAL" if ram.percent > MONITOR_CONFIG["high_ram_threshold"]
                  else "WARNING" if ram.percent > 70
                  else "NORMAL",
    }


# ─────────────────────────────────────────
# 3. DISK MONITORING
# ─────────────────────────────────────────
def get_disk_metrics() -> dict:
    """Returns disk usage and I/O metrics for all partitions."""
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
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
            "read_mb": round(disk_io.read_bytes / (1024 ** 2), 2),
            "write_mb": round(disk_io.write_bytes / (1024 ** 2), 2),
            "read_count": disk_io.read_count,
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
    """
    Measures real HTTP latency to multiple endpoints.
    Falls back to ping if HTTP fails.
    Returns -1.0 only if truly unreachable.
    """
    # Try HTTP first — most accurate and works even when ICMP ping is blocked
    for url in ["https://www.google.com", "https://www.cloudflare.com", "https://one.one.one.one"]:
        try:
            r = requests.get(url, timeout=3)
            return round(r.elapsed.total_seconds() * 1000, 1)
        except Exception:
            continue

    # Fallback: ICMP ping
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

    return -1.0  # truly unreachable


def get_network_metrics() -> dict:
    """Returns network I/O, interface stats, and latency."""
    net_io = psutil.net_io_counters()
    interfaces = {}

    for name, stats in psutil.net_if_stats().items():
        addrs = psutil.net_if_addrs().get(name, [])
        ip = next((a.address for a in addrs if a.family.name == "AF_INET"), "N/A")
        interfaces[name] = {
            "is_up": stats.isup,
            "speed_mbps": stats.speed,
            "mtu": stats.mtu,
            "ip_address": ip,
        }

    latency = get_network_latency_ms(MONITOR_CONFIG["latency_test_host"])

    return {
        "bytes_sent_mb": round(net_io.bytes_sent / (1024 ** 2), 2),
        "bytes_recv_mb": round(net_io.bytes_recv / (1024 ** 2), 2),
        "packets_sent": net_io.packets_sent,
        "packets_recv": net_io.packets_recv,
        "errors_in": net_io.errin,
        "errors_out": net_io.errout,
        "dropped_in": net_io.dropin,
        "dropped_out": net_io.dropout,
        "latency_ms": latency,
        "interfaces": interfaces,
        "status": "CRITICAL" if latency < 0 or latency > 500
                  else "WARNING" if latency > 150
                  else "NORMAL",
    }


# ─────────────────────────────────────────
# 5. PROCESS MONITORING
# ─────────────────────────────────────────
def get_top_processes(n: int = 10) -> list:
    """Returns top N processes by CPU usage."""
    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent",
                                      "memory_percent", "status", "username"]):
        try:
            info = proc.info
            if info["cpu_percent"] is not None:
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu_percent": round(info["cpu_percent"], 2),
                    "memory_percent": round(info["memory_percent"] or 0, 2),
                    "status": info["status"],
                    "user": info["username"] or "N/A",
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:n]


def get_zombie_processes() -> list:
    """Detects zombie/stuck processes."""
    zombies = []
    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                zombies.append({
                    "pid": proc.info["pid"],
                    "name": proc.info["name"],
                    "status": "ZOMBIE",
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return zombies


# ─────────────────────────────────────────
# 6. FULL SYSTEM SNAPSHOT
# ─────────────────────────────────────────
def get_full_system_snapshot() -> dict:
    """
    Returns a complete real-time snapshot of the entire system.
    This is what AREE's ML engine and dashboard consume.
    """
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu": get_cpu_metrics(),
        "ram": get_ram_metrics(),
        "disk": get_disk_metrics(),
        "network": get_network_metrics(),
        "top_processes": get_top_processes(MONITOR_CONFIG["top_processes_count"]),
        "zombie_processes": get_zombie_processes(),
    }

    snapshot["risk_energy"] = compute_system_re(snapshot)
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
    """
    Calculates AREE Risk Energy from real system metrics.

    Formula:
      RE = (CPU*0.35) + (RAM*0.30) + (Disk*0.15) + (Network*0.20)

    Each component normalized to 0-100 scale.
    """
    cpu_score = snapshot["cpu"]["cpu_total_percent"]

    ram_score = snapshot["ram"]["ram_percent"]

    # Disk: use highest usage partition
    disk_parts = snapshot["disk"]["partitions"]
    disk_score = max((p["percent_used"] for p in disk_parts), default=0)

    # Network: normalize latency to 0-100
    latency = snapshot["network"]["latency_ms"]
    if latency < 0:
        # Unknown/unreachable — use neutral score, don't spike RE falsely
        net_score = 50
    else:
        net_score = min(100, (latency / 1000) * 100)

    re = (
        cpu_score  * 0.35 +
        ram_score  * 0.30 +
        disk_score * 0.15 +
        net_score  * 0.20
    )

    return round(re, 2)


# ─────────────────────────────────────────
# 8. CONTINUOUS MONITORING LOOP
# ─────────────────────────────────────────
def start_monitoring_loop(callback=None, stop_event=None):
    """
    Runs continuous monitoring.
    Pass a callback function to receive each snapshot.
    Pass a threading.Event to stop the loop gracefully.
    """
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
                f"Disk={snapshot['disk']['overall_status']} | "
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
    print(f"🌐  Network   : Latency={snap['network']['latency_ms']}ms | Status={snap['network']['status']}")
    print(f"\n🔥  Risk Energy (RE) : {snap['risk_energy']}")
    print(f"📊  System Status    : {snap['overall_status']}")

    print(f"\n🔝 Top Processes:")
    for proc in snap['top_processes'][:5]:
        print(f"    {proc['name']:25s} CPU={proc['cpu_percent']}%  RAM={proc['memory_percent']}%")

    if snap['zombie_processes']:
        print(f"\n⚠️  Zombie Processes: {len(snap['zombie_processes'])} found!")
        for z in snap['zombie_processes']:
            print(f"    PID={z['pid']} Name={z['name']}")
    else:
        print(f"\n✅  No zombie processes detected.")
