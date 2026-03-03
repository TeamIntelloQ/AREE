from aree.re_engine import compute_re, compute_oss, compute_tes
from aree.graph_engine import build_service_graph, compute_dss_graph
from aree.forecaster import forecast_re, should_intervene
from aree.intervention import run_interventions
from aree.rl_loop import rl_decide

# Store previous RE scores for trend detection
_prev_re_map = {}

def run_aree_pipeline(services_data):
    global _prev_re_map

    G = build_service_graph()
    re_map = {}

    # Step 1 — Initial RE per service
    for service, data in services_data.items():
        oss = compute_oss(data.get('metrics', {}))
        tes = compute_tes(data.get('threat', {}))
        re_map[service] = compute_re(oss, tes)

    # Step 2 — Recompute with graph DSS propagation
    for service in re_map:
        oss = compute_oss(services_data[service].get('metrics', {}))
        tes = compute_tes(services_data[service].get('threat', {}))
        dss = compute_dss_graph(G, re_map, service)
        re_map[service] = compute_re(oss, tes, dss)

    # Step 3 — Forecast each service
    forecasts = {}
    for service, re in re_map.items():
        t, forecast = forecast_re(re)
        forecasts[service] = {
            "t": t,
            "re": forecast,
            "intervene": should_intervene(forecast)
        }

    # Step 4 — Rule-based interventions
    interventions = run_interventions(re_map)

    # Step 5 — RL decisions per service
    rl_decisions = {}
    for service, re in re_map.items():
        prev_re = _prev_re_map.get(service, re)
        action, reward = rl_decide(re, prev_re, explore=True)
        rl_decisions[service] = {
            "action": action,
            "reward": reward
        }

    # Update previous RE map for next cycle
    _prev_re_map = dict(re_map)

    return {
        "re_scores":    re_map,
        "forecasts":    forecasts,
        "interventions": interventions,
        "rl_decisions": rl_decisions   # ← NEW
    }

if __name__ == "__main__":
    services_data = {
        "api-gateway":     {"metrics": {"cpu": 0.9, "latency": 500}, "threat": {"ip_score": 0.8}},
        "payment-service": {"metrics": {"cpu": 0.7, "latency": 300}, "threat": {"ip_score": 0.4}},
        "auth-service":    {"metrics": {"cpu": 0.3, "latency": 100}, "threat": {"ip_score": 0.1}},
        "db-primary":      {"metrics": {"cpu": 0.6, "latency": 200}, "threat": {"ip_score": 0.3}}
    }

    result = run_aree_pipeline(services_data)

    print("=" * 50)
    print("  RE SCORES + RL DECISIONS:")
    for s in result['re_scores']:
        re  = result['re_scores'][s]
        rl  = result['rl_decisions'][s]
        print(f"  {s}: RE={re:.2f} | RL={rl['action']} | reward={rl['reward']}")
    print("=" * 50)
