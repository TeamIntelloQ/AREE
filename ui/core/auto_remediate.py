# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime

REMEDIATION_LOG = []

INTERVENTION_PLAYBOOKS = {
    "auth-service":       "Rate limiting enabled + failed auth lockout triggered",
    "payment-gateway":    "Traffic rerouted via api-gateway + circuit breaker opened",
    "user-db":            "Read replicas scaled up + slow query cache cleared",
    "api-gateway":        "Load balancer rebalanced + DDoS filter activated",
    "notification-svc":   "Message queue throttled + retry backoff applied",
    "order-service":      "Order queue paused + dependency health check triggered",
    "inventory-db":       "Connection pool reduced + index optimization queued",
    "logging-svc":        "Log level reduced to ERROR + buffer flush triggered",
}

DEFAULT_PLAYBOOK = "Auto-scaling triggered + entropy cooldown applied"

def auto_remediate(data_df, critical_threshold=70.0):
    df = data_df.copy()
    actions_taken = []
    for idx, row in df.iterrows():
        if row["re_score"] >= critical_threshold:
            old_score = row["re_score"]
            new_score = round(old_score * 0.55, 2)
            df.at[idx, "re_score"] = new_score
            playbook = INTERVENTION_PLAYBOOKS.get(row["service"], DEFAULT_PLAYBOOK)
            action = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "service":   row["service"],
                "re_before": old_score,
                "re_after":  new_score,
                "action":    playbook,
                "severity":  "CRITICAL" if old_score >= 85 else "HIGH",
            }
            actions_taken.append(action)
            REMEDIATION_LOG.append(action)
    return df, actions_taken

def get_remediation_log():
    if not REMEDIATION_LOG:
        return pd.DataFrame(columns=["timestamp","service","re_before","re_after","action","severity"])
    return pd.DataFrame(REMEDIATION_LOG)

def get_system_status(data_df, critical_threshold, warning_threshold):
    avg_re     = data_df["re_score"].mean()
    max_re     = data_df["re_score"].max()
    critical_n = int((data_df["re_score"] >= critical_threshold).sum())
    warning_n  = int((data_df["re_score"] >= warning_threshold).sum())
    if critical_n > 0:
        status = "CRITICAL"
    elif warning_n > 0:
        status = "WARNING"
    else:
        status = "STABLE"
    return {"status": status, "avg_re": round(avg_re,2), "max_re": round(max_re,2),
            "critical_svcs": critical_n, "warning_svcs": warning_n}
