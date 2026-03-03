from aree.re_engine import compute_re, compute_oss, compute_tes, compute_dss
from aree.graph_engine import build_service_graph, compute_dss_graph
from aree.forecaster import forecast_re, should_intervene
from aree.intervention import run_interventions

def run_aree_pipeline(services_data):
    """
    Full AREE pipeline:
    1. Compute RE for each service
    2. Propagate DSS through graph
    3. Forecast RE evolution
    4. Decide interventions
    """
    G = build_service_graph()
    re_map = {}

    # Step 1 — Initial RE per service
    for service, data in services_data.items():
        oss = compute_oss(data.get('metrics', {}))
        tes = compute_tes(data.get('threat', {}))
        re_map[service] = compute_re(oss, tes)

    # Step 2 — Recompute with real DSS propagation
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

    # Step 4 — Interventions
    interventions = run_interventions(re_map)

    return {
        "re_scores": re_map,
        "forecasts": forecasts,
        "interventions": interventions
    }

if __name__ == "__main__":
    import json

    services_data = {
        "api-gateway": {
            "metrics": {"cpu": 0.9, "latency": 500},
            "threat":  {"ip_score": 0.8}
        },
        "payment-service": {
            "metrics": {"cpu": 0.7, "latency": 300},
            "threat":  {"ip_score": 0.4}
        },
        "auth-service": {
            "metrics": {"cpu": 0.3, "latency": 100},
            "threat":  {"ip_score": 0.1}
        },
        "db-primary": {
            "metrics": {"cpu": 0.6, "latency": 200},
            "threat":  {"ip_score": 0.3}
        }
    }

    result = run_aree_pipeline(services_data)

    print("=" * 50)
    print("  RE SCORES:")
    for s, re in result['re_scores'].items():
        print(f"    {s}: {re}")
    print("\n  INTERVENTIONS:")
    for i in result['interventions']:
        print(f"    [{i['severity']}] {i['service']}: {i['action']}")
    print("\n  FORECASTS (will RE exceed 70?):")
    for s, f in result['forecasts'].items():
        print(f"    {s}: intervene={f['intervene']}")
    print("=" * 50)
