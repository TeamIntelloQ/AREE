# intervention.py
from rl_loop import update_weights, log_episode, get_best_action

RULES = [
    {"min_re": 90, "action": "block_ip+restart",  "I_effect": 0.35, "label": "CRITICAL"},
    {"min_re": 70, "action": "scale_replicas",     "I_effect": 0.25, "label": "HIGH"},
    {"min_re": 50, "action": "rate_limit",         "I_effect": 0.15, "label": "MEDIUM"},
    {"min_re":  0, "action": "none",               "I_effect": 0.00, "label": "STABLE"},
]

def choose_action(service, re_value):
    best_past = get_best_action(service)
    for rule in RULES:
        if re_value >= rule["min_re"]:
            action   = rule["action"]
            i_effect = rule["I_effect"]
            label    = rule["label"]
            break
    return {"action": action, "I_effect": i_effect,
            "label": label, "memory_action": best_past}

def apply_intervention(service, re_before, weights, verbose=True):
    result   = choose_action(service, re_before)
    action   = result["action"]
    i_effect = result["I_effect"]
    re_after = max(8.0, re_before - (i_effect * 25))
    re_after = round(re_after, 2)
    new_weights = update_weights(weights, pre_re=re_before, post_re=re_after)
    log_episode(service, re_before, re_after, action, new_weights)
    if verbose:
        print(f"  [{result['label']}] {service:<22} "
              f"RE {re_before:.1f} → {re_after:.1f}  action={action}")
    return re_after, new_weights, action

def intervene_if_needed(re_map, weights, threshold=70, verbose=True):
    updated_re  = re_map.copy()
    updated_w   = weights[:]
    interventions = []
    for svc, re_val in sorted(re_map.items(), key=lambda x: -x[1]):
        if re_val >= threshold:
            re_after, updated_w, action = apply_intervention(
                svc, re_val, updated_w, verbose=verbose)
            updated_re[svc] = re_after
            interventions.append((svc, re_val, re_after, action))
    return updated_re, updated_w, interventions