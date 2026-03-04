import numpy as np

def compute_re_score(service: str, latency: float):
    """AREE Risk Engine - Hackathon MVP"""
    oss = max(0.0, 1.0 - (latency / 2500.0))  # Latency killer
    tes = 0.4 + np.random.uniform(0.0, 0.6)   # Dynamic threats
    re_score = oss * 0.6 + tes * 0.4
    re_score = min(1.0, re_score)
    
    if re_score > 0.7:
        aura_level, action = "🔴 RED", "🚨 AUTO-REMEDIATE"
    elif re_score > 0.4:
        aura_level, action = "🟠 ORANGE", "⚠️ WARNING" 
    else:
        aura_level, action = "🟢 GREEN", "✅ MONITOR"
    
    return {
        "service": service, "oss": oss, "tes": tes,
        "re_score": re_score, "aura_level": aura_level, "action": action
    }

def chaos_test_re_engine():
    print("🚀 AREE RE ENGINE CHAOS TEST")
    alerts = 0
    for i in range(10):
        latency = np.random.uniform(500, 5000)
        result = compute_re_score(f"SVC{i}", latency)
        print(f"{result['service']:<6} Latency={latency:4.0f}ms  "
              f"RE={result['re_score']:.1%}  "
              f"{result['aura_level']}  {result['action']}")
        if result['re_score'] > 0.7:
            alerts += 1
    print(f"\n🎯 {alerts}/10 AUTO-REMEDIATED! 💥")

if __name__ == "__main__":
    chaos_test_re_engine()
