# shared_schema.py — SINGLE SOURCE OF TRUTH FOR ALL MODULES
# Import: from shared_schema import ServicePayload, create_mock_payload

class ServicePayload(dict):
    """Standard dict for ML → Backend → UI flow. Every module reads/writes this."""
    def __init__(self):
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
    payload = ServicePayload()
    payload["service_id"] = service_id
    return payload

# TEST IT WORKS
if __name__ == "__main__":
    test = create_mock_payload("test_svc")
    print("✅ Schema works:", test["service_id"])
