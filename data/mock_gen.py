import random
import json
from faker import Faker

fake = Faker()

SERVICES = ["auth", "api", "db", "cache", "queue", "frontend"]

def generate_event():
    svc = random.choice(SERVICES)
    ip = fake.ipv4()
    oss = 1.0  # FORCE HIGH (was random.uniform(0,1))
    sts = 1.0  # FORCE HIGH (was 0,0.8)
    bcs = 1.0  # FORCE HIGH (was 0,0.5)
    
    return {
        "service": svc,
        "ip": ip,
        "oss": oss,
        "sts": sts,
        "bcs": bcs
    }

# Generate 100 events
events = [generate_event() for _ in range(100)]
print(json.dumps(events[:3], indent=2))  # Sample
# Save sample
with open('sample_events.json', 'w') as f:
    json.dump(events[:10], f, indent=2)
print("✅ Saved data/sample_events.json")
