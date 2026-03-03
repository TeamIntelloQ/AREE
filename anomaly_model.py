import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report
import sqlite3, json

# Load data
df = pd.read_csv("mock_events.csv")
features = df[["cpu", "memory", "req_count", "error_rate"]]

# Train IsolationForest
model = IsolationForest(
    n_estimators=100,
    contamination=0.1,   # expect ~10% anomalies
    random_state=42
)
model.fit(features)

# Predict (-1 = anomaly, 1 = normal)
df["anomaly_raw"] = model.predict(features)
df["anomaly"]     = df["anomaly_raw"].apply(lambda x: 1 if x == -1 else 0)
df["risk_score"]  = model.decision_function(features)
df["risk_score"]  = (df["risk_score"] - df["risk_score"].min()) / \
                    (df["risk_score"].max() - df["risk_score"].min())
df["risk_score"]  = 1 - df["risk_score"]  # flip: higher = riskier

# Results
print("=" * 50)
print("🔍 ANOMALY DETECTION RESULTS")
print("=" * 50)
print(f"Total events    : {len(df)}")
print(f"Anomalies found : {df['anomaly'].sum()}")
print(f"Anomaly rate    : {df['anomaly'].mean()*100:.1f}%")
print()
print("📊 Classification Report:")
print(classification_report(df["is_threat"], df["anomaly"]))

# Top risky services
print("🚨 Top 5 Riskiest Events:")
print(df.nlargest(5, "risk_score")[
    ["service","cpu","memory","risk_score","is_threat"]
])

# Save results
df.to_csv("anomaly_results.csv", index=False)

# Store scores in SQLite
conn = sqlite3.connect("aree_memory.db")
df[["timestamp","service","risk_score","anomaly"]].to_sql(
    "anomaly_scores", conn, if_exists="replace", index=False
)
conn.close()

print("\n✅ Anomaly results saved to anomaly_results.csv")
print("✅ Risk scores stored in aree_memory.db")
