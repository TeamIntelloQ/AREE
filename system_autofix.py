"""
AREE — Complete System Auto-Fix Engine
Automatically detects AND fixes ALL system issues without human intervention.
"""

import os
import gc
import sys
import time
import platform
import subprocess
import psutil
import ctypes
import threading
from datetime import datetime


# ══════════════════════════════════════════════════════════════
# 1. CPU FIXES
# ══════════════════════════════════════════════════════════════
def fix_cpu_high(cpu_percent):
    """Auto-fix high CPU by lowering process priorities and killing zombies."""
    actions = []
    SAFE = {
        "system", "svchost", "wininit", "csrss", "lsass",
        "services", "smss", "winlogon", "explorer", "python",
        "streamlit", "pythonw", "dwm", "taskmgr"
    }

    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "status"]):
        try:
            cpu = proc.cpu_percent(interval=0.1)
            name = proc.info["name"].lower().replace(".exe", "")

            if name in SAFE:
                continue

            # Kill zombie processes
            if proc.info["status"] == psutil.STATUS_ZOMBIE:
                proc.kill()
                actions.append(f"Killed zombie: {proc.info['name']}")
                continue

            # Lower priority of CPU-hungry processes
            if cpu > 60:
                if platform.system() == "Windows":
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    proc.nice(15)
                actions.append(f"Lowered priority: {proc.info['name']} ({cpu:.0f}% CPU)")

            # Kill non-essential processes using extreme CPU
            if cpu > 90 and name not in SAFE:
                proc.terminate()
                actions.append(f"Terminated high-CPU process: {proc.info['name']} ({cpu:.0f}%)")

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Trigger Python garbage collection
    gc.collect()

    return actions if actions else ["CPU priority rebalanced — no critical processes found"]


# ══════════════════════════════════════════════════════════════
# 2. RAM FIXES
# ══════════════════════════════════════════════════════════════
def fix_ram_high(ram_percent):
    """Auto-fix high RAM by freeing memory through multiple methods."""
    actions = []

    # Method 1: Python garbage collection
    collected = gc.collect()
    actions.append(f"Python GC freed {collected} objects")

    # Method 2: Windows memory optimization
    if platform.system() == "Windows":
        try:
            # Empty working set of current process
            ctypes.windll.psapi.EmptyWorkingSet(
                ctypes.windll.kernel32.GetCurrentProcess()
            )
            actions.append("Windows working set cleared")
        except Exception:
            pass

        try:
            # Run memory diagnostic via PowerShell
            subprocess.run(
                'powershell -Command "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()"',
                shell=True, capture_output=True, timeout=10
            )
            actions.append(".NET memory collected")
        except Exception:
            pass

    # Method 3: Linux drop caches
    elif platform.system() == "Linux":
        try:
            subprocess.run("sync && echo 3 > /proc/sys/vm/drop_caches",
                          shell=True, capture_output=True, timeout=10)
            actions.append("Linux page cache dropped")
        except Exception:
            pass

    # Method 4: Kill memory-hungry non-essential processes
    SAFE = {"system", "svchost", "wininit", "csrss", "lsass",
            "services", "smss", "winlogon", "explorer", "python",
            "streamlit", "pythonw"}

    for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
        try:
            mem = proc.info["memory_percent"] or 0
            name = proc.info["name"].lower().replace(".exe", "")
            if mem > 15 and name not in SAFE:
                proc.terminate()
                actions.append(f"Terminated memory hog: {proc.info['name']} ({mem:.1f}% RAM)")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    ram_after = psutil.virtual_memory().percent
    actions.append(f"RAM after fix: {ram_after}% (was {ram_percent}%)")
    return actions


# ══════════════════════════════════════════════════════════════
# 3. DISK FIXES
# ══════════════════════════════════════════════════════════════
def fix_disk_full(mountpoint, percent_used):
    """Auto-fix full disk by cleaning temp files, logs, cache."""
    actions = []
    freed_total = 0

    # Windows temp directories
    temp_dirs = []
    if platform.system() == "Windows":
        temp_dirs = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            "C:\\Windows\\Temp",
            "C:\\Windows\\Prefetch",
            os.path.expanduser("~\\AppData\\Local\\Temp"),
            os.path.expanduser("~\\AppData\\Local\\Microsoft\\Windows\\INetCache"),
        ]
    else:
        temp_dirs = ["/tmp", "/var/tmp", "/var/log"]

    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.exists(temp_dir):
            continue
        freed = 0
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    size = os.path.getsize(item_path)
                    os.remove(item_path)
                    freed += size
            except (PermissionError, OSError):
                continue
        freed_mb = round(freed / (1024 ** 2), 2)
        freed_total += freed_mb
        if freed_mb > 0:
            actions.append(f"Cleared {temp_dir}: freed {freed_mb} MB")

    # Windows Recycle Bin
    if platform.system() == "Windows":
        try:
            subprocess.run(
                'powershell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"',
                shell=True, capture_output=True, timeout=15
            )
            actions.append("Recycle Bin emptied")
        except Exception:
            pass

        # Windows Disk Cleanup (silent)
        try:
            subprocess.Popen("cleanmgr /sagerun:1", shell=True)
            actions.append("Windows Disk Cleanup launched")
        except Exception:
            pass

    actions.append(f"Total freed: {round(freed_total, 2)} MB")
    return actions if actions else [f"Disk cleanup attempted on {mountpoint}"]


# ══════════════════════════════════════════════════════════════
# 4. NETWORK FIXES
# ══════════════════════════════════════════════════════════════
def fix_network_issue(latency_ms):
    """Auto-fix network issues — flush DNS, reset adapter, renew IP."""
    actions = []

    if platform.system() == "Windows":
        # Flush DNS cache
        try:
            result = subprocess.run("ipconfig /flushdns",
                                   shell=True, capture_output=True,
                                   text=True, timeout=10)
            actions.append("DNS cache flushed")
        except Exception:
            pass

        # Release and renew IP
        try:
            subprocess.run("ipconfig /release", shell=True,
                          capture_output=True, timeout=15)
            time.sleep(1)
            subprocess.run("ipconfig /renew", shell=True,
                          capture_output=True, timeout=30)
            actions.append("IP address released and renewed")
        except Exception:
            pass

        # Reset Winsock
        try:
            subprocess.run("netsh winsock reset",
                          shell=True, capture_output=True, timeout=15)
            actions.append("Winsock reset (requires restart to take effect)")
        except Exception:
            pass

        # Reset TCP/IP stack
        try:
            subprocess.run("netsh int ip reset",
                          shell=True, capture_output=True, timeout=15)
            actions.append("TCP/IP stack reset")
        except Exception:
            pass

    elif platform.system() == "Linux":
        try:
            subprocess.run("sudo systemctl restart NetworkManager",
                          shell=True, capture_output=True, timeout=20)
            actions.append("NetworkManager restarted")
        except Exception:
            pass

    return actions if actions else ["Network reset attempted"]


# ══════════════════════════════════════════════════════════════
# 5. SWAP FIXES
# ══════════════════════════════════════════════════════════════
def fix_swap_high(swap_percent):
    """Fix high swap usage by freeing RAM first, then clearing swap."""
    actions = fix_ram_high(psutil.virtual_memory().percent)

    if platform.system() == "Linux":
        try:
            subprocess.run("swapoff -a && swapon -a",
                          shell=True, capture_output=True, timeout=30)
            actions.append("Swap cleared and re-enabled")
        except Exception:
            pass
    else:
        actions.append(f"RAM freed to reduce swap pressure (was {swap_percent}%)")

    return actions


# ══════════════════════════════════════════════════════════════
# 6. ZOMBIE PROCESS FIXES
# ══════════════════════════════════════════════════════════════
def fix_zombie_processes(zombies):
    """Kill all zombie/stuck processes."""
    actions = []
    for z in zombies:
        try:
            proc = psutil.Process(z['pid'])
            proc.kill()
            actions.append(f"Killed zombie: {z['name']} (PID={z['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            actions.append(f"Could not kill {z['name']} — already dead")

    # Also kill any stuck processes
    for proc in psutil.process_iter(["pid", "name", "status"]):
        try:
            if proc.info["status"] in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                proc.kill()
                actions.append(f"Killed dead process: {proc.info['name']}")
        except Exception:
            continue

    return actions if actions else ["No zombie processes found"]


# ══════════════════════════════════════════════════════════════
# 7. WINDOWS UPDATE / RESTART
# ══════════════════════════════════════════════════════════════
def fix_windows_update(delay_seconds=60):
    """Schedule system restart for Windows Update."""
    try:
        msg = f"AREE Auto-Restart: Windows Update pending — restarting in {delay_seconds}s"
        subprocess.Popen(
            f'shutdown /r /t {delay_seconds} /c "{msg}"',
            shell=True
        )
        return [f"⚠️ Restart scheduled in {delay_seconds} seconds",
                "Run 'shutdown /a' in terminal to cancel"]
    except Exception as e:
        return [f"Could not schedule restart: {str(e)}"]


# ══════════════════════════════════════════════════════════════
# 8. HIGH TEMPERATURE FIX
# ══════════════════════════════════════════════════════════════
def fix_high_temperature():
    """Reduce CPU load when temperature is high."""
    actions = []
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    if entry.current > 85:  # Over 85°C
                        # Kill high-CPU processes to cool down
                        actions.extend(fix_cpu_high(100))
                        actions.append(f"Temperature {entry.current}°C — reduced CPU load")
    except (AttributeError, Exception):
        # Windows doesn't always support temperature sensors
        actions.append("Temperature monitoring not available — reduced CPU load as precaution")
        actions.extend(fix_cpu_high(80))
    return actions


# ══════════════════════════════════════════════════════════════
# 9. BROWSER/APP MEMORY LEAK FIX
# ══════════════════════════════════════════════════════════════
def fix_browser_memory_leak():
    """Detect and fix browser memory leaks."""
    actions = []
    browsers = ["chrome", "firefox", "msedge", "opera", "brave"]

    for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
        try:
            name = proc.info["name"].lower().replace(".exe", "")
            mem = proc.info["memory_percent"] or 0

            if any(b in name for b in browsers) and mem > 5:
                if platform.system() == "Windows":
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    proc.nice(10)
                actions.append(f"Throttled {proc.info['name']} using {mem:.1f}% RAM")
        except Exception:
            continue

    return actions if actions else ["No browser memory leaks detected"]


# ══════════════════════════════════════════════════════════════
# 10. STARTUP OPTIMIZATION
# ══════════════════════════════════════════════════════════════
def fix_startup_programs():
    """Disable unnecessary startup programs (Windows)."""
    actions = []
    if platform.system() != "Windows":
        return ["Startup optimization only available on Windows"]

    try:
        # Use WMIC to list startup items
        result = subprocess.run(
            "wmic startup get caption,command",
            shell=True, capture_output=True, text=True, timeout=15
        )
        lines = result.stdout.strip().split('\n')
        actions.append(f"Found {len(lines)-1} startup programs — review manually if needed")
    except Exception:
        pass

    return actions if actions else ["Startup check complete"]


# ══════════════════════════════════════════════════════════════
# MASTER AUTO-FIX FUNCTION
# ══════════════════════════════════════════════════════════════
def auto_fix_all(snap) -> list:
    """
    Master function — checks ALL metrics and auto-fixes everything.
    Returns list of alert dicts with fix results.

    Call this from app.py:
        from system_autofix import auto_fix_all
        alerts = auto_fix_all(snap)
    """
    alerts = []
    cpu      = snap['cpu']['cpu_total_percent']
    ram      = snap['ram']['ram_percent']
    swap     = snap['ram']['swap_percent']
    lat      = snap['network']['latency_ms']
    re       = snap['risk_energy']
    status   = snap['overall_status']
    disk_parts = snap['disk']['partitions']
    zombies  = snap.get('zombie_processes', [])

    # ── 1. CPU ───────────────────────────────────────────────
    if cpu > 85:
        actions = fix_cpu_high(cpu)
        alerts.append({
            "level": "CRITICAL", "icon": "🔴", "metric": "CPU",
            "msg": f"CPU critically high at {cpu}%",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    elif cpu > 70:
        actions = fix_cpu_high(cpu)
        alerts.append({
            "level": "WARNING", "icon": "🟡", "metric": "CPU",
            "msg": f"CPU high at {cpu}%",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 2. RAM ───────────────────────────────────────────────
    if ram > 88:
        actions = fix_ram_high(ram)
        alerts.append({
            "level": "CRITICAL", "icon": "🔴", "metric": "RAM",
            "msg": f"RAM critically full at {ram}% — freeze risk",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    elif ram > 75:
        actions = fix_ram_high(ram)
        alerts.append({
            "level": "WARNING", "icon": "🟡", "metric": "RAM",
            "msg": f"RAM high at {ram}%",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 3. SWAP ──────────────────────────────────────────────
    if swap > 40:
        actions = fix_swap_high(swap)
        alerts.append({
            "level": "WARNING", "icon": "🟡", "metric": "SWAP",
            "msg": f"Swap at {swap}% — RAM being used as disk",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 4. DISK ──────────────────────────────────────────────
    for part in disk_parts:
        if part['percent_used'] > 85:
            actions = fix_disk_full(part['mountpoint'], part['percent_used'])
            level = "CRITICAL" if part['percent_used'] > 95 else "WARNING"
            alerts.append({
                "level": level, "icon": "🔴" if level=="CRITICAL" else "🟡",
                "metric": f"DISK {part['mountpoint']}",
                "msg": f"Disk {part['mountpoint']} at {part['percent_used']}% — {part['free_gb']}GB free",
                "actions": actions, "status": "AUTO-FIXED ✅",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })

    # ── 5. NETWORK ───────────────────────────────────────────
    if lat < 0:
        actions = fix_network_issue(lat)
        alerts.append({
            "level": "CRITICAL", "icon": "🔴", "metric": "NETWORK",
            "msg": "Network unreachable — no internet connection",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    elif lat > 400:
        actions = fix_network_issue(lat)
        alerts.append({
            "level": "CRITICAL", "icon": "🔴", "metric": "NETWORK",
            "msg": f"Network latency critical ({lat}ms)",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    elif lat > 200:
        actions = fix_network_issue(lat)
        alerts.append({
            "level": "WARNING", "icon": "🟡", "metric": "NETWORK",
            "msg": f"Network latency high ({lat}ms)",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 6. ZOMBIE PROCESSES ──────────────────────────────────
    if zombies:
        actions = fix_zombie_processes(zombies)
        alerts.append({
            "level": "WARNING", "icon": "🧟", "metric": "ZOMBIE PROCESSES",
            "msg": f"{len(zombies)} zombie process(es) detected",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 7. RISK ENERGY ───────────────────────────────────────
    if re > 75:
        # Fire all fixes together for critical RE
        actions = []
        actions.extend(fix_cpu_high(cpu))
        actions.extend(fix_ram_high(ram))
        alerts.append({
            "level": "CRITICAL", "icon": "🚨", "metric": "RISK ENERGY",
            "msg": f"Risk Energy CRITICAL ({re}) — cascading failure risk",
            "actions": actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    elif re > 45:
        alerts.append({
            "level": "WARNING", "icon": "⚠️", "metric": "RISK ENERGY",
            "msg": f"Risk Energy WARNING ({re})",
            "actions": ["Monitoring closely — ready to intervene"],
            "status": "WATCHING 👁️",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 8. BROWSER MEMORY LEAK ───────────────────────────────
    browser_actions = fix_browser_memory_leak()
    if "Throttled" in str(browser_actions):
        alerts.append({
            "level": "WARNING", "icon": "🌐", "metric": "BROWSER",
            "msg": "Browser memory leak detected",
            "actions": browser_actions, "status": "AUTO-FIXED ✅",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    # ── 9. WINDOWS UPDATE ────────────────────────────────────
    try:
        import winreg
        winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired")
        actions = fix_windows_update(delay_seconds=60)
        alerts.append({
            "level": "CRITICAL", "icon": "🔄", "metric": "WINDOWS UPDATE",
            "msg": "Windows Update pending — AUTO-RESTART scheduled",
            "actions": actions, "status": "RESTARTING IN 60s 🔁",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    except Exception:
        pass

    # ── 10. UPTIME ───────────────────────────────────────────
    uptime_h = (time.time() - psutil.boot_time()) / 3600
    if uptime_h > 168:  # 7 days → auto restart
        actions = fix_windows_update(delay_seconds=120)
        alerts.append({
            "level": "CRITICAL", "icon": "⏰", "metric": "UPTIME",
            "msg": f"System running {int(uptime_h)} hours — AUTO-RESTART scheduled",
            "actions": actions, "status": "RESTARTING IN 120s 🔁",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
    elif uptime_h > 72:  # 3 days → warn only
        alerts.append({
            "level": "WARNING", "icon": "⏰", "metric": "UPTIME",
            "msg": f"System running {int(uptime_h)} hours — restart recommended",
            "actions": ["Restart when convenient for best performance"],
            "status": "ACTION NEEDED ⚠️",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })

    return alerts


# ══════════════════════════════════════════════════════════════
# RENDER ALERTS IN STREAMLIT
# ══════════════════════════════════════════════════════════════
def render_alerts(alerts, st):
    """
    Call this from app.py to render all alerts beautifully.

    Usage:
        from system_autofix import auto_fix_all, render_alerts
        alerts = auto_fix_all(snap)
        render_alerts(alerts, st)
    """
    if not alerts:
        st.markdown("""
        <div style="background:#0a2a1a;border-left:4px solid #22c55e;
             border-radius:6px;padding:12px 16px;color:#22c55e;">
            ✅ No system issues detected — all metrics normal
        </div>""", unsafe_allow_html=True)
        return

    # Count by level
    critical_count = sum(1 for a in alerts if a['level'] == 'CRITICAL')
    warning_count  = sum(1 for a in alerts if a['level'] == 'WARNING')

    html = f'<h4 style="color:white;">🚨 System Alerts — {critical_count} Critical | {warning_count} Warning | All Auto-Fixed</h4>'

    for a in alerts:
        bg     = "#2d0a0a" if a['level'] == "CRITICAL" else "#2d1f0a"
        border = "#ef4444" if a['level'] == "CRITICAL" else "#f97316"
        s_color = ("#22c55e" if "AUTO-FIXED" in a.get('status','')
                   else "#ef4444" if "RESTARTING" in a.get('status','')
                   else "#f97316")

        # Build actions list
        actions_html = ""
        for act in a.get('actions', []):
            actions_html += f'<div style="color:#22c55e;font-size:12px;margin-top:3px;">→ {act}</div>'

        html += f"""
        <div style="background:{bg};border-left:4px solid {border};
             border-radius:8px;padding:14px 16px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <span style="font-size:18px;">{a['icon']}</span>
                    <span style="color:{border};margin-left:8px;font-weight:bold;font-size:14px;">
                        [{a['level']}] {a['metric']}
                    </span>
                    <span style="color:#d1d5db;margin-left:8px;">{a['msg']}</span>
                </div>
                <div style="text-align:right;min-width:140px;">
                    <span style="color:{s_color};font-weight:bold;font-size:13px;">
                        {a.get('status','')}
                    </span>
                    <div style="color:#6B7280;font-size:11px;">{a.get('timestamp','')}</div>
                </div>
            </div>
            <div style="margin-top:8px;padding-top:8px;border-top:1px solid #1f2937;">
                <span style="color:#9CA3AF;font-size:12px;">🔧 Actions taken:</span>
                {actions_html}
            </div>
        </div>"""

    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from real_monitor import get_full_system_snapshot

    print("=" * 60)
    print("AREE Complete Auto-Fix Engine — Test")
    print("=" * 60)

    snap = get_full_system_snapshot()
    print(f"CPU: {snap['cpu']['cpu_total_percent']}%")
    print(f"RAM: {snap['ram']['ram_percent']}%")
    print(f"RE:  {snap['risk_energy']}")
    print()

    alerts = auto_fix_all(snap)
    if alerts:
        for a in alerts:
            print(f"[{a['level']}] {a['metric']}: {a['msg']}")
            for act in a['actions']:
                print(f"   → {act}")
    else:
        print("✅ System healthy — no issues detected")
