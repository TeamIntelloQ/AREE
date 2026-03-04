"""
Phase 13 — AbuseIPDB Test Script
Run: python test_abuse.py
"""

from services.abuseipdb import check_ip, get_ip_details, check_multiple_ips

# ── Test 1: Basic TES score ───────────────────────────────────────────────────
print("=" * 50)
print("TEST 1 — Google DNS (8.8.8.8) — should be LOW")
print("=" * 50)
score = check_ip("8.8.8.8")
print(f"TES Score: {score}")
print(f"Threat Level: {'HIGH ⚠️' if score > 0.75 else 'MEDIUM 🟡' if score > 0.3 else 'LOW ✅'}")

# ── Test 2: Full details ──────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("TEST 2 — Full IP details for 8.8.8.8")
print("=" * 50)
details = get_ip_details("8.8.8.8")
if details:
    for key, value in details.items():
        print(f"  {key:<22}: {value}")

# ── Test 3: Multiple IPs ──────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("TEST 3 — Check multiple IPs")
print("=" * 50)
ips = ["8.8.8.8", "1.1.1.1"]
results = check_multiple_ips(ips)
for ip, tes in results.items():
    print(f"  {ip:<16} → TES: {tes:.2f}")

print("\n✅ Phase 13 AbuseIPDB tests complete!")