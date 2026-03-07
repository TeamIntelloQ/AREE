import sqlite3
import json

def update_weights(weights, pre_re, post_re, lr=0.1):
    reward = (pre_re - post_re) / 100.0
    updated = [round(w + lr * reward * 0.1, 4) for w in weights]
    total = sum(updated)
    return [round(w / total, 4) for w in updated]

def log_episode(service, pre_re, post_re, action, weights, db_path="aree_memory.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT, pre_re REAL, post_re REAL,
            action TEXT, weights TEXT, reward REAL
        )
    """)
    reward = pre_re - post_re
    conn.execute("INSERT INTO episodes VALUES (NULL,?,?,?,?,?,?)",
        (service, pre_re, post_re, action, json.dumps(weights), reward))
    conn.commit()
    conn.close()

def get_best_action(service, db_path="aree_memory.db"):
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT action FROM episodes WHERE service=? ORDER BY reward DESC LIMIT 1",
        (service,)).fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    w = [0.25, 0.35, 0.25, 0.15]
    new_w = update_weights(w, pre_re=78, post_re=42)
    print("Updated weights:", new_w)
    log_episode("payment-service", 78, 42, "isolate", new_w)
    print("Best action recall:", get_best_action("payment-service"))
def init_db(db_path="aree_memory.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT, pre_re REAL, post_re REAL,
            action TEXT, weights TEXT, reward REAL
        )
    """)
    conn.commit()
    conn.close()