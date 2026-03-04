from services.abuseipdb import check_ip

def calculate_re(ip: str, oss: float, sts: float, bcs: float) -> float:
    tes = check_ip(ip)
    raw_re = 0.25 * (oss + sts + tes + bcs)
    return min(1.0, raw_re)  # THIS LINE FIXES 6375% BUG
