# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap


def build_aura_heatmap(data_df, critical_threshold=75, warning_threshold=45):
    """
    Builds the Risk Aura heatmap.
    Each service is a glowing coloured cell — green/orange/red by RE score.
    """

    services  = data_df["service"].tolist()
    re_scores = data_df["re_score"].tolist()
    n         = len(services)

    # Grid dimensions
    cols = 4
    rows = int(np.ceil(n / cols))

    # Custom aura colormap: deep green → yellow → red
    aura_colors = [
        (0.0,  "#00C896"),   # green  (safe)
        (0.45, "#FFA500"),   # orange (warning)
        (0.75, "#FF4B4B"),   # red    (critical)
        (1.0,  "#FF0000"),   # deep red (extreme)
    ]
    cmap = LinearSegmentedColormap.from_list(
        "aura",
        [(v, c) for v, c in aura_colors]
    )

    fig, ax = plt.subplots(figsize=(12, rows * 2.8))
    fig.patch.set_facecolor("#0E1117")
    ax.set_facecolor("#0E1117")
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.axis("off")

    for i, (svc, score) in enumerate(zip(services, re_scores)):
        row = rows - 1 - (i // cols)
        col = i % cols

        norm_score = score / 100.0
        colour     = cmap(norm_score)

        # Outer glow rectangle (larger, semi-transparent)
        glow = mpatches.FancyBboxPatch(
            (col + 0.04, row + 0.04),
            0.88, 0.82,
            boxstyle="round,pad=0.05",
            linewidth=3,
            edgecolor=colour,
            facecolor=(*colour[:3], 0.15),
            zorder=1
        )
        ax.add_patch(glow)

        # Inner filled rectangle
        inner = mpatches.FancyBboxPatch(
            (col + 0.10, row + 0.10),
            0.76, 0.68,
            boxstyle="round,pad=0.03",
            linewidth=0,
            facecolor=(*colour[:3], 0.55),
            zorder=2
        )
        ax.add_patch(inner)

        # Service name
        ax.text(
            col + 0.50, row + 0.62,
            svc,
            ha="center", va="center",
            fontsize=9, fontweight="bold",
            color="white",
            zorder=3
        )

        # RE Score
        ax.text(
            col + 0.50, row + 0.38,
            f"RE: {score:.1f}",
            ha="center", va="center",
            fontsize=13, fontweight="bold",
            color=colour,
            zorder=3
        )

        # Status label
        if score >= critical_threshold:
            status = "CRITICAL"
        elif score >= warning_threshold:
            status = "WARNING"
        else:
            status = "STABLE"

        ax.text(
            col + 0.50, row + 0.20,
            status,
            ha="center", va="center",
            fontsize=7.5,
            color=colour,
            alpha=0.85,
            zorder=3
        )

    # Legend
    legend_patches = [
        mpatches.Patch(color="#00C896", label=f"STABLE  (RE < {warning_threshold})"),
        mpatches.Patch(color="#FFA500", label=f"WARNING (RE {warning_threshold}-{critical_threshold})"),
        mpatches.Patch(color="#FF4B4B", label=f"CRITICAL (RE > {critical_threshold})"),
    ]
    ax.legend(
        handles=legend_patches,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=3,
        framealpha=0,
        labelcolor="white",
        fontsize=9
    )

    plt.tight_layout()
    return fig
