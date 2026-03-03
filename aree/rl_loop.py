import random

# ─── State Space ────────────────────────────────────────
# State: (re_score_bucket, trend)
# re_score_bucket: 0=LOW, 1=MEDIUM, 2=HIGH
# trend: 0=stable, 1=rising, 2=falling

# ─── Action Space ───────────────────────────────────────
ACTIONS = ["MONITOR", "ALERT", "SCALE_UP", "ISOLATE"]

# ─── Q-Table ────────────────────────────────────────────
# Shape: 3 buckets x 3 trends x 4 actions
Q = {}

def get_state(re_score, prev_re):
    if re_score > 70:
        bucket = 2
    elif re_score > 50:
        bucket = 1
    else:
        bucket = 0

    if re_score > prev_re + 2:
        trend = 1   # rising
    elif re_score < prev_re - 2:
        trend = 2   # falling
    else:
        trend = 0   # stable

    return (bucket, trend)

def get_q(state, action):
    return Q.get((state, action), 0.0)

def best_action(state):
    return max(ACTIONS, key=lambda a: get_q(state, a))

def update_q(state, action, reward, next_state,
             alpha=0.1, gamma=0.9):
    current_q = get_q(state, action)
    best_next = max(get_q(next_state, a) for a in ACTIONS)
    Q[(state, action)] = current_q + alpha * (
        reward + gamma * best_next - current_q
    )

def compute_reward(re_score, action):
    """Reward function — penalize wrong actions."""
    if re_score > 70 and action == "SCALE_UP":   return +10
    if re_score > 70 and action == "MONITOR":     return -10
    if re_score > 50 and action == "ALERT":       return +5
    if re_score < 50 and action == "MONITOR":     return +3
    if re_score < 30 and action == "ISOLATE":     return -5
    return 0  # neutral

def rl_decide(re_score, prev_re, explore=False):
    """
    Given current RE and previous RE,
    return the RL-recommended action.
    explore=True for training, False for inference.
    """
    state = get_state(re_score, prev_re)

    if explore and random.random() < 0.2:
        action = random.choice(ACTIONS)   # epsilon-greedy
    else:
        action = best_action(state)

    reward = compute_reward(re_score, action)
    next_state = get_state(re_score, re_score)  # simplified
    update_q(state, action, reward, next_state)

    return action, reward
