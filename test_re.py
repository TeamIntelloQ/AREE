"""
Phase 14 — RE Engine Test
Run: python test_re.py
"""

from risk_engine import calculate_re

print("=" * 50)
print("TEST 1 — Low risk IP (8.8.8.8 Google DNS)")
print("=" * 50)
re = calculate_re(
    ip="8.8.8.8",
    oss=0.2,
    sts=0.1,
    bcs=0.3,
    entity_name="Google DNS",
    entity_id="ENT-001",
)
print(f"RE Score : {re:.4f}")
print(f"RE %     : {re * 100:.2f}%")
print(f"Risk     : {'HIGH ⚠️  → Slack fired!' if re > 0.75 else 'MEDIUM 🟡' if re > 0.3 else 'LOW ✅'}")

print("\n" + "=" * 50)
print("TEST 2 — High risk simulation")
print("=" * 50)
re2 = calculate_re(
    ip="8.8.8.8",
    oss=0.9,
    sts=0.85,
    bcs=0.8,
    entity_name="Suspicious Entity",
    entity_id="ENT-002",
)
print(f"RE Score : {re2:.4f}")
print(f"RE %     : {re2 * 100:.2f}%")
print(f"Risk     : {'HIGH ⚠️  → Slack fired!' if re2 > 0.75 else 'MEDIUM 🟡' if re2 > 0.3 else 'LOW ✅'}")

print("\n✅ Phase 14 RE Engine tests complete!")