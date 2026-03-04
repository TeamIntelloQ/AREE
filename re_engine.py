<<<<<<< Updated upstream
# re_engine.py — Anirudh's Risk Energy Engine
from shared_schema import ServicePayload, create_mock_payload
import networkx as nx
import numpy as np

def compute_re_score(payload: ServicePayload) -> ServicePayload:
    """Main RE calculation: OSS * TES * propagation_factor"""
    oss = payload["oss_score"]
    tes = payload["tes_score"]

    propagation_factor = 1.2  # TODO: replace with real graph logic

    payload["re_score"] = min(1.0, oss * tes * propagation_factor)

=======
from shared_schema import ServicePayload, create_mock_payload

def compute_re_score(payload):
    oss = payload["oss_score"]
    tes = payload["tes_score"]
    propagation_factor = 1.2
    payload["re_score"] = min(1.0, oss * tes * propagation_factor)
    
>>>>>>> Stashed changes
    if payload["re_score"] > 0.7:
        payload["aura_level"] = "red"
    elif payload["re_score"] > 0.4:
        payload["aura_level"] = "orange"
    else:
        payload["aura_level"] = "green"
<<<<<<< Updated upstream

=======
    
>>>>>>> Stashed changes
    return payload

def test_re_engine():
    payload = create_mock_payload("svc_01")
    payload["oss_score"] = 0.8
    payload["tes_score"] = 0.7
    result = compute_re_score(payload)
<<<<<<< Updated upstream
    print(f"RE Score: {result['re_score']}, Aura: {result['aura_level']}")
=======
    print(f"RE: {result['re_score']}, Aura: {result['aura_level']}")
>>>>>>> Stashed changes

if __name__ == "__main__":
    test_re_engine()
