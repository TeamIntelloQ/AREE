import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ABUSEIPDB_API_KEY")

# ─── Fallback mock data if no API key ───────────────────
MOCK_THREATS = {
    "api-gateway":     0.8,
    "payment-service": 0.4,
    "auth-service":    0.1,
    "db-primary":      0.3
}

# Known suspicious IPs per service (demo purposes)
SERVICE_IPS = {
    "api-gateway":     "118.25.6.39",
    "payment-service": "185.220.101.1",
    "auth-service":    "8.8.8.8",
    "db-primary":      "45.33.32.156"
}

def fetch_ip_threat_score(ip: str) -> float:
    """
    Hit AbuseIPDB API for a given IP.
    Returns normalized score 0.0 - 1.0
    Falls back to 0.5 on error.
    """
    if not API_KEY or API_KEY == "your_api_key_here":
        print(f"[threat_feed] No API key — using mock data")
        return None

    try:
        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={
                "Key": API_KEY,
                "Accept": "application/json"
            },
            params={
                "ipAddress": ip,
                "maxAgeInDays": 90
            },
            timeout=5
        )
        data = response.json()
        score = data["data"]["abuseConfidenceScore"]
        return round(score / 100.0, 3)   # normalize to 0-1

    except Exception as e:
        print(f"[threat_feed] API error for {ip}: {e}")
        return 0.5   # safe fallback

def get_threat_scores() -> dict:
    """
    Returns threat scores for all services.
    Uses real API if key exists, mock data otherwise.
    """
    scores = {}
    for service, ip in SERVICE_IPS.items():
        real_score = fetch_ip_threat_score(ip)
        if real_score is not None:
            scores[service] = real_score
            print(f"[threat_feed] {service} ({ip}): {real_score}")
        else:
            scores[service] = MOCK_THREATS[service]
    return scores

if __name__ == "__main__":
    print("Testing threat feed...")
    scores = get_threat_scores()
    for svc, score in scores.items():
        print(f"  {svc}: {score}")
