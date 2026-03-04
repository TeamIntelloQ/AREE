"""
Phase 15 — Test Slack Alert via RE Engine
Run: python test_alert.py
"""

from risk_engine import calculate_re

print("=" * 50)
print("TEST — Force HIGH RE score → trigger Slack alert")
print("=" * 50)

re = calculate_re(
    ip="8.8.8.8",
    oss=1.0,
    sts=1.0,
    bcs=1.0,
    entity_name="Test Entity",
    entity_id="ENT-TEST-001",
)

print(f"RE Score : {re:.4f}")
print(f"RE %     : {re * 100:.2f}%")

if re * 100 >= 75:
    print("Risk     : HIGH ⚠️  → Slack alert fired!")
else:
    print("Risk     : MEDIUM/LOW — no alert sent")

print("\n✅ Phase 15 test complete!")