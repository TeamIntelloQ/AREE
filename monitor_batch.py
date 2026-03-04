import json
from services.alerts import monitor_ip

events = json.load(open('data/sample_events.json'))

alerts = []
services_re = {}

for e in events:
    re_pct = monitor_ip(e["ip"], e["oss"], e["sts"], e["bcs"], e["service"])
    services_re[e["service"]] = re_pct / 100
    
    if re_pct > 75:
        alerts.append(e['service'])

print(f"\n🚨 HIGH RISK Alerts: {alerts}")
print(f"📈 Max RE: {max(services_re.values()):.1%}")
