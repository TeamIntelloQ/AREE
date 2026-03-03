import sqlite3
import datetime

def get_intervention(re_score, service_name):
    """Decide action based on RE level"""
    if re_score >= 80:
        action = "ISOLATE"
        severity = "CRITICAL"
    elif re_score >= 70:
        action = "SCALE_UP"
        severity = "HIGH"
    elif re_score >= 50:
        action = "ALERT"
        severity = "MEDIUM"
    else:
        action = "MONITOR"
        severity = "LOW"

    return {
        "service": service_name,
        "action": action,
        "severity": severity,
        "re_score": re_score,
        "timestamp": str(datetime.datetime.now())
    }

def log_intervention(intervention, db_path="aree/incidents.db"):
    """Store to SQLite for incident memory"""
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS incidents
        (service TEXT, action TEXT, severity TEXT,
         re_score REAL, timestamp TEXT)""")
    conn.execute("INSERT INTO incidents VALUES (?,?,?,?,?)", (
        intervention['service'],
        intervention['action'],
        intervention['severity'],
        intervention['re_score'],
        intervention['timestamp']
    ))
    conn.commit()
    conn.close()

def run_interventions(service_re_map):
    """Run through all services, decide + log actions"""
    results = []
    for service, re in service_re_map.items():
        decision = get_intervention(re, service)
        log_intervention(decision)
        results.append(decision)
    return sorted(results, key=lambda x: -x['re_score'])

if __name__ == "__main__":
    mock = {
        "api-gateway": 82,
        "payment-service": 71,
        "auth-service": 48,
        "db-primary": 55,
        "redis-cache": 22,
        "notification-service": 66
    }
    actions = run_interventions(mock)
    print("=" * 45)
    for a in actions:
        print(f"  [{a['severity']}] {a['service']}: {a['action']} (RE={a['re_score']})")
    print("=" * 45)
