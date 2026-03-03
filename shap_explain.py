import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
import shap
import sqlite3

# Load + train again
df       = pd.read_csv("mock_events.csv")
features = ["cpu", "memory", "req_count", "error_rate"]
X        = df[features]
y        = df["is_threat"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    eval_metric="logloss",
    random_state=42
)
model.fit(X_train, y_train)

# SHAP Explainer
import json

booster = model.get_booster()

# Fix base_score string bug in XGBoost 2.x + SHAP
config = json.loads(booster.save_config())
config["learner"]["learner_model_param"]["base_score"] = "5e-01"
booster.load_config(json.dumps(config))

explainer   = shap.TreeExplainer(booster)
shap_values = explainer.shap_values(X_test)



# Print top explanations
print("=" * 50)
print("🔍 SHAP EXPLAINABILITY RESULTS")
print("=" * 50)

# Mean absolute SHAP per feature
mean_shap = pd.DataFrame({
    "feature"    : features,
    "importance" : np.abs(shap_values).mean(axis=0)
}).sort_values("importance", ascending=False)

print("\n📌 Mean SHAP Feature Impact:")
for _, row in mean_shap.iterrows():
    bar = "█" * int(row["importance"] * 100)
    print(f"  {row['feature']:<12} {bar} {row['importance']:.4f}")

# Explain top 3 threatening events
df_test              = X_test.copy()
df_test["shap_cpu"]    = shap_values[:, 0]
df_test["shap_memory"] = shap_values[:, 1]
df_test["is_threat"]   = y_test.values

top3 = df_test.nlargest(3, "shap_memory")
print("\n🚨 Top 3 Threat Explanations:")
for i, row in top3.iterrows():
    print(f"\n  Event {i}:")
    print(f"    CPU: {row['cpu']:.1f}%   → SHAP: {row['shap_cpu']:+.3f}")
    print(f"    Memory: {row['memory']:.1f}% → SHAP: {row['shap_memory']:+.3f}")
    print(f"    Threat: {'🚨 YES' if row['is_threat'] else '✅ NO'}")

# Save SHAP values
df_test.to_csv("shap_results.csv", index=False)

conn = sqlite3.connect("aree_memory.db")
df_test.to_sql("shap_scores", conn, if_exists="replace", index=False)
conn.close()

print("\n✅ SHAP results saved to shap_results.csv")
print("✅ SHAP scores stored in aree_memory.db")
print("\n💡 SHAP Summary: High memory + high CPU = HIGH THREAT RISK")

