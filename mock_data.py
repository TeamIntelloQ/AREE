import pandas as pd
import numpy as np
from faker import Faker
import sqlite3, random

fake = Faker()
random.seed(42)
np.random.seed(42)

SERVICES = [f"service_{i}" for i in range(1, 11)]

def generate_events(n=1000):
    events = []
    for _ in range(n):
        cpu    = round(random.uniform(10, 100), 2)
        memory = round(random.uniform(20, 95), 2)

        if random.random() < 0.1:
            cpu    = round(random.uniform(85, 100), 2)
            memory = round(random.uniform(88, 99), 2)

        event = {
            "timestamp"  : fake.date_time_this_month().isoformat(),
            "service"    : random.choice(SERVICES),
            "ip"         : fake.ipv4(),
            "cpu"        : cpu,
            "memory"     : memory,
            "req_count"  : random.randint(100, 5000),
            "error_rate" : round(random.uniform(0, 0.3), 3),
            "is_threat"  : 1 if cpu > 85 and memory > 88 else 0
        }
        events.append(event)
    return pd.DataFrame(events)

df = generate_events(1000)
df.to_csv("mock_events.csv", index=False)

conn = sqlite3.connect("aree_memory.db")
df.to_sql("events", conn, if_exists="replace", index=False)
conn.close()

print(f"✅ Generated {len(df)} events")
print(f"🚨 Threats found: {df['is_threat'].sum()}")
print(f"📊 Sample:\n{df.head(3)}")

