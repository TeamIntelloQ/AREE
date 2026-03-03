import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import sqlite3

# Load data
df = pd.read_csv("mock_events.csv")
features = ["cpu", "memory", "req_count", "error_rate"]
X = df[features]
y = df["is_threat"]

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train XGBoost
model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42
)
model.fit(X_train, y_train)

# Predict
y_pred  = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

# Results
print("=" * 50)
print("🎯 XGBOOST THREAT SCORING RESULTS")
print("=" * 50)
print(f"Training samples : {len(X_train)}")
print(f"Testing samples  : {len(X_test)}")
print()
print("📊 Classification Report:")
print(classification_report(y_test, y_pred))

# Cross validation
cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"🔁 Cross-Val Accuracy: {cv_scores.mean()*100:.1f}% ± {cv_scores.std()*100:.1f}%")

# Feature importance
print("\n📌 Feature Importance:")
for feat, imp in zip(features, model.feature_importances_):
    bar = "█" * int(imp * 50)
    print(f"  {feat:<12} {bar} {imp:.3f}")

# Save threat scores
df_test         = X_test.copy()
df_test["actual"]       = y_test.values
df_test["predicted"]    = y_pred
df_test["threat_score"] = y_proba
df_test.to_csv("threat_scores.csv", index=False)

# Store in SQLite
conn = sqlite3.connect("aree_memory.db")
df_test.to_sql("threat_scores", conn, if_exists="replace", index=False)
conn.close()

print("\n✅ Threat scores saved to threat_scores.csv")
print("✅ Scores stored in aree_memory.db")
