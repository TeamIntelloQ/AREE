from risk_engine import calculate_re  # Create if missing
from services.slack_alerts import send_slack
from services.remediate import auto_remediate  # Phase 21
import logging
import os

logging.basicConfig(filename='incidents.log', level=logging.INFO, 
                   format='%(asctime)s - %(message)s')

def monitor_ip(ip: str, oss: float, sts: float, bcs: float, service: str = "unknown") -> float:
    re = calculate_re(ip, oss, sts, bcs)  # Phase 14
    re_pct = re * 100
    
    print(f"📊 {service} ({ip}): {re_pct:.1f}%", end=" ") 
    
    if re > 0.70:
        msg = f"🚨 HIGH RISK: {service}/{ip} RE={re_pct:.1f}%"
        logging.info(msg)
        send_slack(msg)
        print("→ SLACK!")
        
        if auto_remediate(service, re_pct):  # AUTO-FIX!
            print("✅ REMEDIATED!")
    else:
        risk = "🟢 LOW" if re_pct < 30 else "🟡 MEDIUM"
        print(f"{risk}")
    
    return re_pct
