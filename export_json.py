import os
import pandas as pd
import sqlite3
import json
import numpy as np
import warnings
warnings.filterwarnings("ignore")

def forecast_moving_average(re_history, steps=5, window=5):
    history = np.array(re_history)
    if len(history) < 2:
        return np.array([history[-1]] * steps)
    window  = min(window, len(history))
    ma      = np.mean(history[-window:])
    trend   = (history[-1] - history[-window]) / window
    future  = [ma + trend * (i + 1) for i in range(steps)]
    return np.clip(future, 0, 100)

def forecast_all_services(csv_path, steps=5):
    df = pd.read_csv(csv_path)
    forecasts = {}
    for svc in df["service"].unique():
        history = df[df["service"] == svc].sort_values("t")["RE"].tolist()
        forecasts[svc] = forecast_moving_average(history, steps)
    return forecasts

os.makedirs("frontend/data", exist_ok=True)

df = pd.read_csv("re_computed.csv")
df.to_json("frontend/data/risk_energy.json", orient="records", indent=2)

summary = {
    "peak_re":         round(float(df.RE.max()), 1),
    "peak_service":    df.loc[df.RE.idxmax(), "service"],
    "avg_re":          round(float(df.RE.mean()), 1),
    "total_services":  int(df.service.nunique()),
    "total_timesteps": int(df.t.nunique())
}
with open("frontend/data/summary.json", "w") as f:
    json.dump(summary, f, indent=2)

pd.read_csv("anomaly_results.csv").to_json(
    "frontend/data/anomalies.json", orient="records", indent=2)

pd.read_csv("threat_scores.csv").to_json(
    "frontend/data/threats.json", orient="records", indent=2)

forecasts = forecast_all_services("re_computed.csv", steps=5)
result = {svc: list(map(float, vals)) for svc, vals in forecasts.items()}
with open("frontend/data/forecast.json", "w") as f:
    json.dump(result, f, indent=2)

conn = sqlite3.connect("aree_memory.db")
df_ep = pd.read_sql("SELECT * FROM episodes ORDER BY id DESC LIMIT 50", conn)
conn.close()
df_ep.to_json("frontend/data/interventions.json", orient="records", indent=2)

print("✅ All JSON files exported to frontend/data/")
print(f"   peak_re      = {summary['peak_re']}")
print(f"   peak_service = {summary['peak_service']}")
print(f"   services     = {summary['total_services']}")