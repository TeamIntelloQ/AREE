# generate_mock_data.py 
import pandas as pd
import numpy as np

np.random.seed(42)

SERVICES = ["auth", "payment", "checkout", "database", "api_gateway", "logging"]

# Business Criticality (static)
BCS = {
    "auth": 0.8,
    "payment": 0.9,
    "checkout": 0.7,
    "database": 0.85,
    "api_gateway": 0.6,
    "logging": 0.3
}

# Dependency graph weights (who depends on whom)
DEPS = {
    "payment":     {"auth": 0.7},
    "checkout":    {"payment": 0.6, "auth": 0.5},
    "api_gateway": {"auth": 0.4},
    "database":    {},
    "auth":        {"database": 0.5},
    "logging":     {}
}

records = []

re_scores = {s: 10.0 for s in SERVICES}  # Start stable

for t in range(60):
    attack = 10 <= t <= 40  # Attack window
    intervention = t >= 42  # AREE intervenes

    new_re = {}

    for svc in SERVICES:
        # OSS: CPU/latency anomaly
        if svc == "auth" and attack:
            oss = np.random.uniform(0.6, 0.9)
        else:
            oss = np.random.uniform(0.05, 0.2)

        # TES: Threat signals
        if svc == "auth" and attack:
            brute_force = min(1.0, (t - 9) / 20.0)  # Builds up
            bad_ip      = 0.85 * 0.8 if t >= 12 else 0.0
            tes = min(1.0, brute_force * 0.7 + bad_ip)
        else:
            tes = np.random.uniform(0.0, 0.1)

        # DSS: Propagate from dependencies
        dss = 0.0
        for dep, weight in DEPS.get(svc, {}).items():
            dss += weight * (re_scores[dep] / 100.0) * 0.8

        dss = min(1.0, dss)
        bcs = BCS[svc]

        # RE formula (full version)
        re_raw = (oss * 0.25 + tes * 0.25 + dss * 0.25 + bcs * 0.25)

        # Intervention
        I = 0.15 if (intervention and svc in ["auth", "payment"]) else 0.0

        # Time evolution with entropy decay
        lam = 0.03
        re_new = re_scores[svc] + (re_raw * 100) - (I * 100) - (lam * re_scores[svc])
        re_new = max(0, min(100, re_new))
        new_re[svc] = re_new

        records.append({
            "t": t,
            "service": svc,
            "OSS": round(oss, 4),
            "TES": round(tes, 4),
            "DSS": round(dss, 4),
            "BCS": round(bcs, 4),
            "RE": round(re_new, 2),
            "attack": attack,
            "intervention": intervention
        })

    re_scores = new_re  # Update for next timestep

df = pd.DataFrame(records)
df.to_csv("aree_mock_simulation.csv", index=False)
print(f"✅ CSV generated: {len(df)} rows")
print(df[df['service']=='auth'][['t','OSS','TES','DSS','RE']].tail(10))
