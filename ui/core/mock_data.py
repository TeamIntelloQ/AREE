# -*- coding: utf-8 -*-
import random
import pandas as pd
from faker import Faker

fake = Faker()
random.seed(42)

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

def generate_service_metrics(n_services=8):
    """Generate mock CPU, memory, error rate metrics per service."""
    data = []
    for svc in SERVICES[:n_services]:
        data.append({
            "service":      svc,
            "cpu":          round(random.uniform(10, 95), 2),
            "memory":       round(random.uniform(20, 90), 2),
            "error_rate":   round(random.uniform(0, 25), 2),
            "latency_ms":   round(random.uniform(50, 800), 2),
            "req_per_sec":  random.randint(50, 1000),
        })
    return pd.DataFrame(data)


def generate_threat_ips(n=20):
    """Generate mock suspicious IP addresses with threat scores."""
    data = []
    for _ in range(n):
        data.append({
            "ip":            fake.ipv4_public(),
            "country":       fake.country(),
            "threat_score":  random.randint(0, 100),
            "attack_type":   random.choice([
                                "DDoS", "BruteForce",
                                "SQLi", "XSS", "PortScan"
                             ]),
            "hit_count":     random.randint(1, 500),
        })
    return pd.DataFrame(data)


def generate_incident_log(n=15):
    """Generate mock incident log entries."""
    severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    data = []
    for _ in range(n):
        data.append({
            "timestamp":    fake.date_time_this_month().strftime("%Y-%m-%d %H:%M:%S"),
            "service":      random.choice(SERVICES),
            "severity":     random.choice(severity_levels),
            "description":  random.choice([
                                "Spike in error rate detected",
                                "Unusual traffic pattern",
                                "Memory threshold exceeded",
                                "Failed auth attempts",
                                "Latency anomaly detected",
                                "Config drift observed",
                            ]),
        })
    return pd.DataFrame(data).sort_values("timestamp", ascending=False)


def compute_re_scores(metrics_df, threat_df):
    """
    Compute a basic Risk Energy score per service.
    RE = 0.4*CPU + 0.3*ErrorRate + 0.2*Latency(normalized) + 0.1*ThreatExposure
    Scale: 0 to 100
    """
    re_scores = []
    avg_threat = threat_df["threat_score"].mean()

    for _, row in metrics_df.iterrows():
        oss  = (row["cpu"] / 100) * 40
        dss  = (row["error_rate"] / 25) * 30
        lat  = (row["latency_ms"] / 800) * 20
        tes  = (avg_threat / 100) * 10
        re   = round(oss + dss + lat + tes, 2)
        re_scores.append(re)

    metrics_df = metrics_df.copy()
    metrics_df["re_score"] = re_scores
    return metrics_df
def get_intervention_suggestions(data_df, critical_threshold=75, warning_threshold=45):
    """Returns AI-style intervention suggestions per critical/warning service."""
    suggestions = []
    for _, row in data_df.iterrows():
        svc   = row["service"]
        score = row["re_score"]

        if score >= critical_threshold:
            suggestions.append({
                "service":    svc,
                "re_score":   score,
                "status":     "CRITICAL",
                "action":     "Isolate service immediately",
                "suggestion": f"Scale down {svc}, reroute traffic via api-gateway, "
                              f"trigger incident response playbook. RE={score:.1f} exceeds threshold."
            })
        elif score >= warning_threshold:
            suggestions.append({
                "service":    svc,
                "re_score":   score,
                "status":     "WARNING",
                "action":     "Monitor and throttle",
                "suggestion": f"Increase resource allocation for {svc}, "
                              f"enable rate limiting. RE={score:.1f} approaching critical."
            })

    return pd.DataFrame(suggestions) if suggestions else pd.DataFrame()

