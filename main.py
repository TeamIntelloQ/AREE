# main.py — AREE Full Pipeline Entry Point
#
# Run order:
#   python generate_real_data.py   ← creates aree_simulation_v2.csv
#   python anomaly_model.py        ← creates anomaly_results.csv
#   python xgboost_model.py        ← creates threat_scores.csv
#   python main.py                 ← runs everything below
#
# Outputs:
#   re_computed.csv                ← RE per service per timestep
#   re_evolution.png               ← Risk Energy chart
#   re_heatmap.png                 ← Service heatmap

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import warnings
warnings.filterwarnings("ignore")
from rl_loop import init_db
init_db()  # ensures episodes table exists before intervention runs

from risk_energy  import load_and_compute, build_dependency_graph, summarize
from forecast     import forecast_all_services
from intervention import intervene_if_needed


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Compute Risk Energy from simulation CSV
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "█"*55)
print("  AREE — AUTONOMOUS RISK EVOLUTION ENGINE")
print("█"*55)

print("\n[1/4] Computing Risk Energy across all services...")
df = load_and_compute("aree_simulation_v2.csv")
df.to_csv("re_computed.csv", index=False)
print(f"  ✅ re_computed.csv — {len(df)} rows")
summarize(df)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Forecast future RE per service
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2/4] Forecasting future Risk Energy...")
forecasts = forecast_all_services("re_computed.csv", steps=5)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Intervention loop (apply interventions where RE ≥ 70)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3/4] Running Intervention Engine on peak timestep...")

# Get peak timestep
peak_t = df.loc[df.RE.idxmax(), "t"]
peak_snapshot = df[df.t == peak_t].set_index("service")["RE"].to_dict()

weights = [0.25, 0.35, 0.25, 0.15]

print(f"\n  Peak at t={peak_t}:")
for svc, re in sorted(peak_snapshot.items(), key=lambda x: -x[1]):
    print(f"    {svc:<22} RE={re:.1f}")

print("\n  Interventions:")
updated_re, updated_w, interventions = intervene_if_needed(
    peak_snapshot, weights, threshold=70
)
print(f"\n  Updated RL weights: {updated_w}")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Visualize
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4/4] Generating visualizations...")

SERVICES  = df["service"].unique()
COLORS    = {
    "auth_service":      "#ff3c6e",
    "payment_service":   "#ff8c42",
    "checkout_service":  "#ffd700",
    "frontend":          "#00f0ff",
    "cart_service":      "#c77dff",
    "database":          "#7fff6e",
}

# ── Plot 1: RE Evolution Over Time ─────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10),
                          facecolor="#04050d", gridspec_kw={"height_ratios": [3, 1]})

ax = axes[0]
ax.set_facecolor("#04050d")
ax.tick_params(colors="#4a5a80")
for spine in ax.spines.values():
    spine.set_edgecolor("#1a2540")

for svc in SERVICES:
    svc_df = df[df.service == svc].sort_values("t")
    color  = COLORS.get(svc, "#ffffff")
    ax.plot(svc_df.t, svc_df.RE, label=svc, color=color,
            linewidth=2, alpha=0.9)
    # Shade forecast
    last_t  = svc_df.t.max()
    preds   = forecasts.get(svc, [])
    f_times = list(range(int(last_t) + 1, int(last_t) + 1 + len(preds)))
    ax.plot(f_times, preds, color=color, linewidth=1.5,
            linestyle="--", alpha=0.5)

# Intervention line
intervention_t = df[df.intervention == True]["t"].min()
if not pd.isna(intervention_t):
    ax.axvline(intervention_t, color="#00f0ff", linewidth=1.5,
               linestyle=":", alpha=0.6, label=f"Intervention (t={int(intervention_t)})")

# Threshold line
ax.axhline(90, color="#ff3c6e", linewidth=1, linestyle="--", alpha=0.4)
ax.text(1, 91, "Cascade Threshold (90)", color="#ff3c6e",
        fontsize=8, alpha=0.7)

ax.set_title("AREE — Risk Energy Evolution per Service",
             color="#c8d8f0", fontsize=13, pad=12)
ax.set_xlabel("Timestep (minutes)", color="#4a5a80")
ax.set_ylabel("Risk Energy (0–100)",  color="#4a5a80")
ax.legend(fontsize=8, facecolor="#080c18", labelcolor="#c8d8f0",
          edgecolor="#1a2540", loc="upper left")
ax.set_ylim(0, 105)
ax.grid(True, color="#1a2540", linewidth=0.5, alpha=0.6)

# ── Plot 2: Phase bar ──────────────────────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor("#04050d")
ax2.tick_params(colors="#4a5a80")
for spine in ax2.spines.values():
    spine.set_edgecolor("#1a2540")

auth_df = df[df.service == "auth_service"].sort_values("t")
phase_colors = {"stable": "#1a2540", "attack": "#ff3c6e", "recovery": "#00f0ff"}
for _, row in auth_df.iterrows():
    ax2.bar(row.t, 1, color=phase_colors.get(row.phase, "#333"), width=1)

ax2.set_yticks([])
ax2.set_xlabel("Timestep", color="#4a5a80")
ax2.set_title("Attack Phase (auth_service)", color="#4a5a80",
              fontsize=9, pad=4)

plt.tight_layout(pad=2.0)
plt.savefig("re_evolution.png", dpi=150, facecolor="#04050d",
            bbox_inches="tight")
plt.close()
print("  ✅ re_evolution.png saved")


# ── Plot 2: Service RE Heatmap ─────────────────────────────────────────────
pivot = df.pivot_table(index="service", columns="t", values="RE")

fig, ax = plt.subplots(figsize=(16, 5), facecolor="#04050d")
ax.set_facecolor("#04050d")

cmap = mcolors.LinearSegmentedColormap.from_list(
    "risk", ["#1a2540", "#ffd700", "#ff3c6e"]
)
im = ax.imshow(pivot.values, aspect="auto", cmap=cmap,
               vmin=0, vmax=100)

ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, color="#c8d8f0", fontsize=9)
ax.set_xlabel("Timestep (minutes)", color="#4a5a80")
ax.set_title("AREE — Risk Energy Heatmap (All Services)",
             color="#c8d8f0", fontsize=12, pad=10)
ax.tick_params(colors="#4a5a80")

cbar = plt.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
cbar.set_label("Risk Energy", color="#4a5a80")
cbar.ax.yaxis.set_tick_params(color="#4a5a80")
plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#4a5a80")

# Mark intervention
if not pd.isna(intervention_t):
    ax.axvline(intervention_t - pivot.columns.min(), color="#00f0ff",
               linewidth=2, linestyle="--", alpha=0.7)

plt.tight_layout()
plt.savefig("re_heatmap.png", dpi=150, facecolor="#04050d",
            bbox_inches="tight")
plt.close()
print("  ✅ re_heatmap.png saved")


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "█"*55)
print("  PIPELINE COMPLETE")
print("█"*55)
print("  re_computed.csv    ← RE values per service per timestep")
print("  re_evolution.png   ← RE time-series chart")
print("  re_heatmap.png     ← service heatmap")
print("  aree_memory.db     ← RL intervention memory")
print("█"*55 + "\n")
