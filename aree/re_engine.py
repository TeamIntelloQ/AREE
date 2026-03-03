import numpy as np
from aree.graph_engine import build_service_graph, compute_dss_graph

G = build_service_graph()

def compute_oss(metrics):
    cpu = metrics.get('cpu', 0)
    latency = metrics.get('latency', 0)
    oss = 1 - (cpu * 0.6 + (latency / 1000) * 0.4)
    return round(max(0.0, min(1.0, oss)), 4)

def compute_tes(threat):
    return round(float(threat.get('ip_score', 0.0)), 4)

def compute_dss(service_re_map=None, node="api-gateway"):
    if service_re_map is None:
        return 0.5
    return compute_dss_graph(G, service_re_map, node)

def compute_bcs():
    return 0.8

def compute_re(oss, tes, dss=None, bcs=None, weights=None):
    if dss is None: dss = 0.5
    if bcs is None: bcs = compute_bcs()
    if weights is None: weights = [0.25, 0.25, 0.25, 0.25]
    re = (oss * weights[0] +
          tes * weights[1] +
          dss * weights[2] +
          bcs * weights[3])
    return round(float(np.clip(re * 100, 0, 100)), 2)


if __name__ == "__main__":
    metrics = {"cpu": 0.85, "latency": 400}
    threat  = {"ip_score": 0.9}
    service_re_map = {
        "payment-service": 80,
        "db-primary": 65,
        "auth-service": 30,
        "redis-cache": 20,
        "notification-service": 50,
        "api-gateway": 45,
        "ml-model-service": 35
    }

    oss = compute_oss(metrics)
    tes = compute_tes(threat)
    dss = compute_dss(service_re_map, "api-gateway")
    bcs = compute_bcs()
    re  = compute_re(oss, tes, dss, bcs)

    print("=" * 40)
    print(f"  OSS  (stability)  : {oss}")
    print(f"  TES  (threat)     : {tes}")
    print(f"  DSS  (graph real) : {dss}")
    print(f"  BCS  (criticality): {bcs}")
    print(f"  ➜ RE Score        : {re} / 100")
    print("=" * 40)
    if re >= 70:
        print("  ⚠️  HIGH RISK — intervention needed!")
    elif re >= 50:
        print("  🟡 MEDIUM RISK — monitor closely.")
    else:
        print("  ✅ LOW RISK — stable.")
