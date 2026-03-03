import numpy as np

def compute_oss(metrics):
    """
    Operational Stability Score — how stable is the service?
    Inputs: cpu (0.0–1.0), latency (ms)
    Output: 0.0 (unstable) to 1.0 (fully stable)
    """
    cpu = metrics.get('cpu', 0)
    latency = metrics.get('latency', 0)
    oss = 1 - (cpu * 0.6 + (latency / 1000) * 0.4)
    return round(max(0.0, min(1.0, oss)), 4)

def compute_tes(threat):
    """
    Threat Exposure Score — how exposed is the service to threats?
    Input: ip_score from AbuseIPDB (0.0–1.0)
    Output: 0.0 (safe) to 1.0 (fully exposed)
    """
    return round(float(threat.get('ip_score', 0.0)), 4)

def compute_dss():
    """
    Dependency Sensitivity Score — STUB for now.
    Will be replaced with real NetworkX graph propagation in Phase 2.
    """
    return 0.5

def compute_bcs():
    """
    Business Criticality Score — static for now.
    Higher = more critical service.
    """
    return 0.8

def compute_re(oss, tes, dss=None, bcs=None, weights=None):
    """
    Master RE equation — Risk Energy (0 to 100 scale)
    Combines all four scores with equal weights by default.
    """
    if dss is None: dss = compute_dss()
    if bcs is None: bcs = compute_bcs()
    if weights is None: weights = [0.25, 0.25, 0.25, 0.25]

    re = (oss * weights[0] +
          tes * weights[1] +
          dss * weights[2] +
          bcs * weights[3])
    return round(float(np.clip(re * 100, 0, 100)), 2)


# ── Quick self-test ──────────────────────────────────────────
if __name__ == "__main__":
    # Simulate a high-stress service under threat
    metrics = {"cpu": 0.85, "latency": 400}
    threat  = {"ip_score": 0.9}

    oss = compute_oss(metrics)
    tes = compute_tes(threat)
    dss = compute_dss()
    bcs = compute_bcs()
    re  = compute_re(oss, tes, dss, bcs)

    print("=" * 40)
    print(f"  OSS  (stability) : {oss}")
    print(f"  TES  (threat)    : {tes}")
    print(f"  DSS  (dep stub)  : {dss}")
    print(f"  BCS  (criticality): {bcs}")
    print(f"  ➜ RE Score       : {re} / 100")
    print("=" * 40)
    if re >= 70:
        print("  ⚠️  HIGH RISK — intervention needed!")
    elif re >= 50:
        print("  🟡 MEDIUM RISK — monitor closely.")
    else:
        print("  ✅ LOW RISK — stable.")
