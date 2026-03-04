"""
Phase 14 — RE Engine with AbuseIPDB TES Integration
Feeds live TES scores into Risk Evolution calculation.
"""

import logging
from services.abuseipdb import check_ip
from aree.slack_alerts import send_re_alert

logger = logging.getLogger(__name__)

OSS_WEIGHT = 0.25
STS_WEIGHT = 0.25
TES_WEIGHT = 0.25
BCS_WEIGHT = 0.25

RE_ALERT_THRESHOLD = 0.74


def calculate_re(
    ip: str,
    oss: float,
    sts: float,
    bcs: float,
    entity_name: str = "Unknown Entity",
    entity_id: str = "N/A",
) -> float:

    tes = check_ip(ip)

    re = (OSS_WEIGHT * oss) + (STS_WEIGHT * sts) + (TES_WEIGHT * tes) + (BCS_WEIGHT * bcs)

    logger.info(
        "RE calculated | IP: %s | OSS: %.2f | STS: %.2f | TES: %.2f | BCS: %.2f | RE: %.2f",
        ip, oss, sts, tes, bcs, re,
    )

    re_percent = re * 100
    if re_percent >= RE_ALERT_THRESHOLD * 100:
        send_re_alert(
            re_score=re_percent,
            entity_name=entity_name,
            entity_id=entity_id,
            extra_context={
                "IP Address": ip,
                "TES (AbuseIPDB)": f"{tes:.2f}",
                "OSS": f"{oss:.2f}",
                "STS": f"{sts:.2f}",
                "BCS": f"{bcs:.2f}",
            },
        )

    return re