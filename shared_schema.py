<<<<<<< Updated upstream
# shared_schema.py — SINGLE SOURCE OF TRUTH FOR ALL MODULES
# Import: from shared_schema import ServicePayload, create_mock_payload
=======
# shared_schema.py — SINGLE SOURCE OF TRUTH FOR ALL MODULES (FULL VERSION)
# Import everywhere: from shared_schema import ServicePayload, create_mock_payload
>>>>>>> Stashed changes

class ServicePayload(dict):
    """Standard dict for ML → Backend → UI flow. Every module reads/writes this."""
    def __init__(self):
<<<<<<< Updated upstream
        self["service_id"] = None           # "svc_01"
        self["oss_score"] = 0.0             # ML: Operational Stability [0-1]
        self["tes_score"] = 0.0             # ML: Threat Exposure [0-1]  
        self["re_score"] = 0.0              # Backend: Risk Energy [0-1]
        self["forecast"] = []               # Backend: list of [time, RE] points
        self["shap_values"] = {}            # ML: {"feature1": 0.3, ...}
        self["aura_level"] = "green"        # UI: "green", "orange", "red"
        self["intervention"] = False        # Backend: auto-remediation triggered?

def create_mock_payload(service_id: str = "svc_01") -> ServicePayload:
    """Instant test payload for debugging every module."""
=======
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
>>>>>>> Stashed changes
    payload = ServicePayload()
    payload["service_id"] = service_id
    return payload

<<<<<<< Updated upstream
# TEST IT WORKS
=======
# TEST IT WORKS (line 45+ preserved)
>>>>>>> Stashed changes
if __name__ == "__main__":
    test = create_mock_payload("test_svc")
    print("✅ Schema works:", test["service_id"])
