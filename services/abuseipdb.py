"""
Phase 13 — AbuseIPDB Integration
Pulls real IP threat data and converts to TES score for RE calculation.
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
ABUSEIPDB_KEY: str = os.getenv("ABUSEIPDB_KEY", "")
ABUSEIPDB_URL: str = "https://api.abuseipdb.com/api/v2/check"
MAX_AGE_IN_DAYS: int = 90


def check_ip(ip: str, max_age_in_days: int = MAX_AGE_IN_DAYS) -> float:
    """
    Check an IP address against AbuseIPDB.
    Returns TES score as float between 0.0 and 1.0
    """
    import requests

    if not ABUSEIPDB_KEY:
        raise ValueError("ABUSEIPDB_KEY is not set. Add it to your .env file.")

    params = {
        "ipAddress": ip,
        "maxAgeInDays": max_age_in_days,
        "verbose": True,
    }
    headers = {
        "Key": ABUSEIPDB_KEY,
        "Accept": "application/json",
    }

    try:
        resp = requests.get(ABUSEIPDB_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()["data"]
        abuse_score = data["abuseConfidenceScore"]
        tes_score = abuse_score / 100.0

        logger.info(
            "IP %s — abuseConfidenceScore: %d, TES: %.2f, ISP: %s, Country: %s",
            ip,
            abuse_score,
            tes_score,
            data.get("isp", "N/A"),
            data.get("countryCode", "N/A"),
        )

        return tes_score

    except requests.exceptions.Timeout:
        logger.error("AbuseIPDB request timed out for IP: %s", ip)
        return 0.0
    except requests.exceptions.HTTPError as e:
        logger.error("AbuseIPDB HTTP error: %s", e)
        return 0.0
    except (KeyError, ValueError) as e:
        logger.error("AbuseIPDB response parse error: %s", e)
        return 0.0
    except Exception as e:
        logger.exception("Unexpected error checking IP %s: %s", ip, e)
        return 0.0


def get_ip_details(ip: str, max_age_in_days: int = MAX_AGE_IN_DAYS) -> Optional[dict]:
    """
    Get full IP details from AbuseIPDB.
    Returns full data dict or None on error.
    """
    import requests

    if not ABUSEIPDB_KEY:
        raise ValueError("ABUSEIPDB_KEY is not set. Add it to your .env file.")

    params = {
        "ipAddress": ip,
        "maxAgeInDays": max_age_in_days,
        "verbose": True,
    }
    headers = {
        "Key": ABUSEIPDB_KEY,
        "Accept": "application/json",
    }

    try:
        resp = requests.get(ABUSEIPDB_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()["data"]

        return {
            "ip":               data.get("ipAddress"),
            "is_public":        data.get("isPublic"),
            "abuse_confidence": data.get("abuseConfidenceScore"),
            "tes_score":        data.get("abuseConfidenceScore", 0) / 100.0,
            "country":          data.get("countryCode"),
            "isp":              data.get("isp"),
            "domain":           data.get("domain"),
            "total_reports":    data.get("totalReports"),
            "last_reported_at": data.get("lastReportedAt"),
            "is_tor":           data.get("isTor", False),
            "is_whitelisted":   data.get("isWhitelisted", False),
        }

    except Exception as e:
        logger.exception("Error fetching IP details for %s: %s", ip, e)
        return None


def check_multiple_ips(ip_list: list) -> dict:
    """
    Check multiple IPs and return a dict of {ip: tes_score}.
    """
    results = {}
    for ip in ip_list:
        results[ip] = check_ip(ip)
    return results