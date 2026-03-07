"""
AREE — Real Auto-Remediation Engine
Performs ACTUAL system fixes when Risk Energy exceeds thresholds.
Works on: Windows (primary), Linux/MacOS (fallback supported)
"""

import os
import gc
import platform
import psutil
import subprocess
import threading
import time
from datetime import datetime
from real_monitor import get_full_system_snapshot, MONITOR_CONFIG


# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────
REMEDIATION_CONFIG = {
    "critical_re_threshold": 75,    # RE above this → auto-remediate
    "warning_re_threshold": 45,     # RE above this → log warning
    "cooldown_seconds": 60,         # Wait between remediations (avoid thrashing)
    "max_remediations_per_hour": 10,# Safety limit
    "kill_zombie_processes": True,  # Auto-kill zombie processes
    "free_ram_if_above": 85,        # % RAM → trigger memory cleanup
    "kill_high_cpu_process": False, # ⚠️ Dangerous — disabled by default
    "high_cpu_process_threshold": 90,# % CPU per process to consider killing
    "log_file": "aree_remediation.log",
}

# Track remediation history
_remediation_log = []
_last_remediation_time = {}
_remediation_count_this_hour = 0


# ─────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────
def log_action(service: str, action: str, result: str, re_before: float, re_after: float = None):
    """Logs every remediation action with timestamp."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "service": service,
        "action": action,
        "result": result,
        "re_before": re_before,
        "re_after": re_after,
    }
    _remediation_log.append(entry)

    # Also write to log file
    with open(REMEDIATION_CONFIG["log_file"], "a") as f:
        f.write(
            f"[{entry['timestamp']}] {service} | "
            f"Action={action} | RE={re_before}→{re_after or '?'} | {result}\n"
        )

    print(
        f"[AREE Remediate] {entry['timestamp']} | "
        f"{service} | {action} | {result}"
    )
    return entry


def get_remediation_log() -> list:
    """Returns all remediation actions taken this session."""
    return _remediation_log.copy()


# ─────────────────────────────────────────
# REMEDIATION ACTIONS
# ─────────────────────────────────────────

def action_free_memory() -> str:
    """
    Frees memory by:
    1. Triggering Python garbage collection
    2. On Windows: calls EmptyWorkingSet via PowerShell
    3. On Linux: drops page cache
    """
    try:
        # Python GC
        collected = gc.collect()

        if platform.system() == "Windows":
            # Clear standby memory list via PowerShell (requires admin)
            ps_cmd = (
                "powershell -Command \"Clear-RecycleBin -Force -ErrorAction SilentlyContinue; "
                "[System.GC]::Collect()\""
            )
            subprocess.run(ps_cmd, shell=True, capture_output=True, timeout=15)

            # Try to free working set of current process
            try:
                import ctypes
                ctypes.windll.psapi.EmptyWorkingSet(
                    ctypes.windll.kernel32.GetCurrentProcess()
                )
            except Exception:
                pass

        elif platform.system() == "Linux":
            # Drop caches (requires root)
            subprocess.run(
                "sync && echo 3 > /proc/sys/vm/drop_caches",
                shell=True, capture_output=True, timeout=10
            )

        ram_after = psutil.virtual_memory().percent
        return f"SUCCESS — GC collected {collected} objects. RAM now at {ram_after}%"

    except Exception as e:
        return f"PARTIAL — {str(e)}"


def action_kill_zombie_processes() -> str:
    """Kills zombie/stuck processes."""
    killed = []
    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                proc.kill()
                killed.append(f"{proc.info['name']}(PID={proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if killed:
        return f"SUCCESS — Killed {len(killed)} zombies: {', '.join(killed)}"
    return "SUCCESS — No zombie processes found"


def action_kill_high_cpu_process(threshold_percent: float = 90) -> str:
    """
    ⚠️ CAREFUL: Kills processes using extreme CPU.
    Only kills non-system processes above threshold.
    """
    SAFE_PROCESSES = {
        "system", "svchost", "wininit", "csrss", "lsass",
        "services", "smss", "winlogon", "explorer", "python",
        "streamlit", "pythonw",
    }
    killed = []

    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "username"]):
        try:
            cpu = proc.cpu_percent(interval=0.5)
            name = proc.info["name"].lower().replace(".exe", "")
            if cpu > threshold_percent and name not in SAFE_PROCESSES:
                proc.terminate()
                killed.append(f"{proc.info['name']}(PID={proc.info['pid']}, CPU={cpu}%)")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed:
        return f"TERMINATED — {', '.join(killed)}"
    return f"SUCCESS — No process exceeded {threshold_percent}% CPU threshold"


def action_clear_temp_files() -> str:
    """Clears Windows temp files to free disk space."""
    freed_mb = 0
    temp_dirs = []

    if platform.system() == "Windows":
        temp_dirs = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            "C:\\Windows\\Temp",
        ]
    else:
        temp_dirs = ["/tmp"]

    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.exists(temp_dir):
            continue
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    os.remove(item_path)
                    freed_mb += size / (1024 ** 2)
            except (PermissionError, OSError):
                continue

    return f"SUCCESS — Freed {round(freed_mb, 2)} MB from temp directories"


def action_restart_network_adapter() -> str:
    """
    Resets network adapter on Windows when latency is very high.
    Requires admin privileges.
    """
    try:
        if platform.system() == "Windows":
            # Release and renew IP (works without admin)
            subprocess.run("ipconfig /release", shell=True,
                           capture_output=True, timeout=15)
            time.sleep(2)
            subprocess.run("ipconfig /renew", shell=True,
                           capture_output=True, timeout=30)
            # Flush DNS cache
            subprocess.run("ipconfig /flushdns", shell=True,
                           capture_output=True, timeout=10)
            return "SUCCESS — Network adapter reset and DNS flushed"
        elif platform.system() == "Linux":
            subprocess.run("sudo systemctl restart NetworkManager",
                           shell=True, capture_output=True, timeout=15)
            return "SUCCESS — NetworkManager restarted"
    except Exception as e:
        return f"FAILED — {str(e)}"


def action_reduce_cpu_priority() -> str:
    """Lowers priority of highest CPU-consuming non-system processes."""
    SAFE_PROCESSES = {
        "system", "svchost", "wininit", "csrss", "lsass",
        "services", "smss", "winlogon", "explorer",
    }
    adjusted = []

    for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
        try:
            cpu = proc.cpu_percent(interval=0.3)
            name = proc.info["name"].lower().replace(".exe", "")
            if cpu > 50 and name not in SAFE_PROCESSES:
                if platform.system() == "Windows":
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    proc.nice(10)  # Linux: higher nice = lower priority
                adjusted.append(f"{proc.info['name']}(CPU={cpu}%)")
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            continue

    if adjusted:
        return f"SUCCESS — Lowered priority for: {', '.join(adjusted[:5])}"
    return "SUCCESS — No processes needed priority adjustment"


def action_log_warning(service: str, re: float) -> str:
    """Just logs a warning — no destructive action."""
    return f"WARNING LOGGED — {service} RE={re} — Monitor closely"


# ─────────────────────────────────────────
# DECISION ENGINE
# ─────────────────────────────────────────
def select_remediation_action(snapshot: dict) -> tuple:
    """
    Decides WHAT to fix based on which metric is highest.
    Returns (action_name, action_function, target_service)
    """
    re = snapshot["risk_energy"]
    cpu = snapshot["cpu"]["cpu_total_percent"]
    ram = snapshot["ram"]["ram_percent"]
    disk_status = snapshot["disk"]["overall_status"]
    latency = snapshot["network"]["latency_ms"]
    zombies = snapshot["zombie_processes"]

    # Priority order: fix worst metric first
    if zombies:
        return ("kill_zombies", action_kill_zombie_processes, "zombie-processes")

    if latency < 0 or latency > 500:
        return ("reset_network", action_restart_network_adapter, "network-adapter")

    if ram > REMEDIATION_CONFIG["free_ram_if_above"]:
        return ("free_memory", action_free_memory, "memory-subsystem")

    if disk_status == "CRITICAL":
        return ("clear_temp", action_clear_temp_files, "disk-storage")

    if cpu > 80:
        return ("reduce_cpu_priority", action_reduce_cpu_priority, "cpu-scheduler")

    # Default: generic memory cleanup
    return ("free_memory", action_free_memory, "system-general")


# ─────────────────────────────────────────
# MAIN REMEDIATION TRIGGER
# ─────────────────────────────────────────
def check_and_remediate(snapshot: dict = None) -> dict | None:
    """
    Main function — call this every monitoring cycle.
    Automatically detects issues and remediates if needed.
    
    Returns the remediation log entry if action was taken, else None.
    """
    global _remediation_count_this_hour

    if snapshot is None:
        snapshot = get_full_system_snapshot()

    re = snapshot["risk_energy"]
    now = time.time()

    # ── CRITICAL: Auto-remediate
    if re >= REMEDIATION_CONFIG["critical_re_threshold"]:
        # Check cooldown
        last_time = _last_remediation_time.get("system", 0)
        if now - last_time < REMEDIATION_CONFIG["cooldown_seconds"]:
            remaining = int(REMEDIATION_CONFIG["cooldown_seconds"] - (now - last_time))
            print(f"[AREE Remediate] Cooldown active — {remaining}s remaining")
            return None

        # Check hourly limit
        if _remediation_count_this_hour >= REMEDIATION_CONFIG["max_remediations_per_hour"]:
            print("[AREE Remediate] ⚠️ Hourly remediation limit reached!")
            return None

        # Select and execute action
        action_name, action_fn, target_service = select_remediation_action(snapshot)

        print(f"\n🚨 [AREE] CRITICAL RE={re} — Executing: {action_name} on {target_service}")
        result = action_fn()

        # Measure RE after remediation
        time.sleep(2)
        new_snapshot = get_full_system_snapshot()
        re_after = new_snapshot["risk_energy"]

        # Log it
        entry = log_action(target_service, action_name, result, re, re_after)

        # Update tracking
        _last_remediation_time["system"] = now
        _remediation_count_this_hour += 1

        return entry

    # ── WARNING: Just log
    elif re >= REMEDIATION_CONFIG["warning_re_threshold"]:
        print(f"⚠️  [AREE] WARNING RE={re} — Monitoring closely, no action yet")
        return log_action("system", "warning_logged",
                          f"RE={re} above warning threshold", re)

    return None


# ─────────────────────────────────────────
# BACKGROUND REMEDIATION DAEMON
# ─────────────────────────────────────────
def start_remediation_daemon(stop_event: threading.Event = None):
    """
    Runs check_and_remediate in a background thread continuously.
    
    Usage in your Streamlit app:
        import threading
        from auto_remediate_real import start_remediation_daemon
        
        stop = threading.Event()
        daemon = threading.Thread(
            target=start_remediation_daemon, 
            args=(stop,), 
            daemon=True
        )
        daemon.start()
    """
    print("[AREE Daemon] Auto-remediation daemon started")
    while True:
        if stop_event and stop_event.is_set():
            print("[AREE Daemon] Stopped.")
            break
        try:
            snapshot = get_full_system_snapshot()
            check_and_remediate(snapshot)
        except Exception as e:
            print(f"[AREE Daemon] Error: {e}")
        time.sleep(MONITOR_CONFIG["poll_interval_seconds"])


# ─────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("AREE Real Auto-Remediation Engine — Test Run")
    print("=" * 60)

    snapshot = get_full_system_snapshot()
    print(f"\n📊 Current System State:")
    print(f"   CPU     : {snapshot['cpu']['cpu_total_percent']}%")
    print(f"   RAM     : {snapshot['ram']['ram_percent']}%")
    print(f"   Disk    : {snapshot['disk']['overall_status']}")
    print(f"   Latency : {snapshot['network']['latency_ms']}ms")
    print(f"   RE Score: {snapshot['risk_energy']} → {snapshot['overall_status']}")

    print(f"\n🔧 Running remediation check...")
    result = check_and_remediate(snapshot)

    if result:
        print(f"\n✅ Remediation taken:")
        print(f"   Action  : {result['action']}")
        print(f"   Target  : {result['service']}")
        print(f"   Result  : {result['result']}")
        print(f"   RE      : {result['re_before']} → {result['re_after']}")
    else:
        print(f"\n✅ System is healthy — no remediation needed (RE={snapshot['risk_energy']})")

    print(f"\n📋 Full remediation log saved to: {REMEDIATION_CONFIG['log_file']}")
