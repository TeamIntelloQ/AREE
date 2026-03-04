#!/usr/bin/env python3
"""
shared_schema.py — SINGLE SOURCE OF TRUTH FOR ALL MODULES (FULL VERSION)
Import everywhere: from shared_schema import ServicePayload, create_mock_payload
"""

class ServicePayload(dict):
    """Standard dict for ML → Backend → UI flow. Every module reads/writes this."""
    def __init__(self):
        self["service_id"] = None           # e.g., "svc_01"
        self["oss_score"] = 0.0             # ML: Operational Stability Score [0-1]
        self["tes_score"] = 0.0             # ML: Threat Exposure Score [0-1]
        self["re_score"] = 0.0              # Backend: Risk Energy [0-1]
        self["forecast"] = []               # Backend: [t, RE(t)] curve
        self["shap_values"] = {}            # ML: feature importance dict
        self["aura_level"] = "green"        # UI: "green/orange/red"
        self["intervention"] = False        # Backend: auto-action triggered?

def create_mock_payload(service_id: str = "svc_01") -> ServicePayload:
    """Quick test payload for debugging every module."""
    payload = ServicePayload()
    payload["service_id"] = service_id
    return payload

# TEST IT WORKS
if __name__ == "__main__":
    test = create_mock_payload("test_svc")
    print("✅ Schema works:", test["service_id"])
    print("Full payload:", dict(test))
