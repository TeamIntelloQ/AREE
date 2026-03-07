# -*- coding: utf-8 -*-
# real_metrics.py — reads LIVE metrics from your laptop
import psutil
import random

SERVICES = [
    "auth-service",
    "payment-gateway",
    "user-db",
    "api-gateway",
    "notification-svc",
    "order-service",
    "inventory-db",
    "logging-svc",
]

def get_real_metrics(n_services=8):
    """
    Pulls real CPU, memory, network stats from THIS machine.
    Each service gets the real system baseline + small random variation
    so they look like separate services.
    """
    import pandas as pd

    # FIX 1: Single CPU reading with interval=1 for accuracy (matches real_monitor.py)
    real_cpu    = psutil.cpu_percent(interval=1)
    real_memory = psutil.virtual_memory().percent
    net         = psutil.net_io_counters()
    real_net    = min((net.bytes_sent + net.bytes_recv) / 1_000_000, 100)

    rows = []
    for svc in SERVICES[:n_services]:
        variation  = random.uniform(-8, 8)
        cpu        = max(0, min(100, real_cpu    + variation))
        memory     = max(0, min(100, real_memory + variation))
        latency    = 50 + (cpu / 100) * 750 + random.uniform(-20, 20)
        error_rate = max(0, (cpu - 60) / 40 * 25) if cpu > 60 else random.uniform(0, 3)

        rows.append({
            "service":     svc,
            "cpu":         round(cpu, 2),
            "memory":      round(memory, 2),
            "error_rate":  round(error_rate, 2),
            "latency_ms":  round(latency, 2),
            "req_per_sec": random.randint(50, 1000),
        })

    return pd.DataFrame(rows)


def compute_re_from_real(metrics_df):
    """Compute RE scores from real system metrics."""
    re_scores = []
    for _, row in metrics_df.iterrows():
        oss = (row["cpu"] / 100) * 40
        dss = (row["error_rate"] / 25) * 30
        lat = (row["latency_ms"] / 800) * 20
        # FIX 2: Removed random noise — RE score is now deterministic and stable
        re  = round(min(oss + dss + lat, 100), 2)
        re_scores.append(re)

    metrics_df = metrics_df.copy()
    metrics_df["re_score"] = re_scores
    return metrics_df
