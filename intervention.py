# intervention.py — Intervention Trigger + RL Integration
# Reads:   current RE per service
# Outputs: action taken, I_effect (fed back into RE evolution)
# Logs:    every episode into aree_memory.db via rl_loop.py

from rl_loop import update_weights, log_episode, get_best_action

# ── Intervention Rules ────────────────────────────────────────────────────────
# Thresholds matching your hackathon spec
RULES = [
    {"min_re": 90, "action": "block_ip+restart",  "I_effect": 0.35, "label": "CRITICAL"},
    {"min_re": 70, "action": "scale_replicas",     "I_effect": 0.25, "label": "HIGH"},
    {"min_re": 50, "action": "rate_limit",         "I_effect": 0.15, "label": "MEDIUM"},
    {"min_re":  0, "action": "none",               "I_effect": 0.00, "label": "STABLE"},
]


def choose_action(service, re_value):
    """
    Rule-based action selection.
    Checks rl_loop memory first — if a better historical action exists, uses it.
    Returns: dict with action, I_effect, label
    """
    # Check memory for best historical action for this service
    best_past = get_best_action(service)

    # Select rule-based action
    for rule in RULES:
        if re_value >= rule["min_re"]:
            action   = rule["action"]
            i_effect = rule["I_effect"]
            label    = rule["label"]
            break

    return {
        "action":        action,
        "I_effect":      i_effect,
        "label":         label,
        "memory_action": best_past   # what worked before (for display)
    }


def apply_intervention(service, re_before, weights, verbose=True):
    """
    Full intervention cycle:
    1. Choose action
    2. Compute RE reduction
    3. Log episode to aree_memory.db
    4. Update RL weights
    Returns: re_after, updated_weights, action_taken
    """
    result   = choose_action(service, re_before)
    action   = result["action"]
    i_effect = result["I_effect"]

    # Simulated RE reduction from intervention
    re_after = max(8.0, re_before - (i_effect * 25))
    re_after = round(re_after, 2)

    # RL weight update (reward = risk reduced)
    new_weights = update_weights(weights, pre_re=re_before, post_re=re_after)

    # Log to aree_memory.db
    log_episode(service, re_before, re_after, action, new_weights)

    if verbose:
        print(f"  [{result['label']}] {service:<22} "
              f"RE {re_before:.1f} → {re_after:.1f}  "
              f"action={action}  ΔRE=-{re_before - re_after:.1f}")
        if result["memory_action"] and result["memory_action"] != action:
            print(f"    💡 Memory suggests: {result['memory_action']}")

    return re_after, new_weights, action


# ── Batch intervention over all services at a timestep ───────────────────────
def intervene_if_needed(re_map, weights, threshold=70, verbose=True):
    """
    re_map:    dict {service: RE_value}
    threshold: RE level above which we intervene
    Returns:   updated re_map, updated weights
    """
    updated_re  = re_map.copy()
    updated_w   = weights[:]
    interventions = []

    for svc, re_val in sorted(re_map.items(), key=lambda x: -x[1]):
        if re_val >= threshold:
            re_after, updated_w, action = apply_intervention(
                svc, re_val, updated_w, verbose=verbose
            )
            updated_re[svc] = re_after
            interventions.append((svc, re_val, re_after, action))

    return updated_re, updated_w, interventions


# ── Run standalone ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Example: simulate a single intervention step
    re_map  = {
        "auth_service":     88.5,
        "payment_service":  74.2,
        "checkout_service": 61.0,
        "frontend":         35.0,
        "cart_service":     28.0,
        "database":         20.0
    }
    weights = [0.25, 0.35, 0.25, 0.15]

    print("\n" + "="*55)
    print("  INTERVENTION ENGINE")
    print("="*55)
    updated_re, updated_w, interventions = intervene_if_needed(re_map, weights)
    print(f"\n  Updated weights: {updated_w}")
    print(f"  Total interventions: {len(interventions)}")
