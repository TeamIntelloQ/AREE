# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def generate_re_history(data_df, timesteps=20, scenario="Normal Operations"):
    records = []
    scenario_multiplier = {
        "Normal Operations":  1.0,
        "DDoS Attack":        1.5,
        "Config Drift":       1.2,
        "Brute Force":        1.3,
        "Data Exfiltration":  1.6,
    }.get(scenario, 1.0)

    np.random.seed(None)

    for _, row in data_df.iterrows():
        base_re = float(row["re_score"]) / scenario_multiplier
        svc     = str(row["service"])
        current = base_re * 0.4

        for t in range(timesteps):
            noise   = np.random.uniform(-3, 5)
            current = current + (base_re - current) * 0.18 + noise
            current = float(np.clip(current, 0, 100))
            records.append({
                "timestep": int(t),
                "service":  svc,
                "re_score": round(current, 2),
            })

    return pd.DataFrame(records)


def generate_forecast(history_df, forecast_steps=8):
    records  = []
    last_t   = int(history_df["timestep"].max())
    services = history_df["service"].unique()

    for svc in services:
        svc_data  = history_df[history_df["service"] == svc]
        last_vals = svc_data.tail(5)["re_score"].values
        trend     = (last_vals[-1] - last_vals[0]) / max(len(last_vals) - 1, 1)
        last_re   = float(svc_data["re_score"].iloc[-1])

        for i in range(1, forecast_steps + 1):
            forecasted = float(np.clip(
                last_re + trend * i + np.random.uniform(-1, 1), 0, 100
            ))
            records.append({
                "timestep": last_t + i,
                "service":  svc,
                "re_score": round(forecasted, 2),
            })

    return pd.DataFrame(records)


def build_timeline_chart(data_df, scenario="Normal Operations",
                         critical_threshold=75, warning_threshold=45):

    history_df  = generate_re_history(data_df, timesteps=20, scenario=scenario)
    forecast_df = generate_forecast(history_df, forecast_steps=8)

    services = data_df["service"].tolist()
    re_now   = dict(zip(data_df["service"].tolist(), data_df["re_score"].tolist()))

    fig = go.Figure()

    for svc in services:
        score = float(re_now.get(svc, 50))

        if score >= critical_threshold:
            colour = "#FF4B4B"
        elif score >= warning_threshold:
            colour = "#FFA500"
        else:
            colour = "#00C896"

        svc_hist = history_df[history_df["service"] == svc].copy()
        svc_fore = forecast_df[forecast_df["service"] == svc].copy()

        # Historical line
        fig.add_trace(go.Scatter(
            x=list(svc_hist["timestep"]),
            y=list(svc_hist["re_score"]),
            mode="lines",
            name=svc,
            line=dict(color=colour, width=2.5),
            hovertemplate=f"<b>{svc}</b><br>T=%{{x}}<br>RE=%{{y:.1f}}<extra></extra>"
        ))

        # Forecast line
        fig.add_trace(go.Scatter(
            x=list(svc_fore["timestep"]),
            y=list(svc_fore["re_score"]),
            mode="lines",
            name=f"{svc} forecast",
            line=dict(color=colour, width=1.5, dash="dot"),
            opacity=0.55,
            showlegend=False,
            hovertemplate=f"<b>{svc} forecast</b><br>T=%{{x}}<br>RE=%{{y:.1f}}<extra></extra>"
        ))

    # Threshold lines
    fig.add_hline(
        y=critical_threshold,
        line_dash="dash", line_color="#FF4B4B",
        annotation_text=f"Critical ({critical_threshold})",
        annotation_font_color="#FF4B4B",
        opacity=0.6
    )
    fig.add_hline(
        y=warning_threshold,
        line_dash="dash", line_color="#FFA500",
        annotation_text=f"Warning ({warning_threshold})",
        annotation_font_color="#FFA500",
        opacity=0.6
    )

    # Forecast zone
    last_hist_t = int(history_df["timestep"].max())
    fig.add_vrect(
        x0=last_hist_t, x1=last_hist_t + 8,
        fillcolor="#2a2a3a", opacity=0.3,
        layer="below", line_width=0,
        annotation_text="Forecast Zone",
        annotation_font_color="#888888",
        annotation_position="top left"
    )

    fig.update_layout(
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        font=dict(color="white", family="monospace"),
        title=dict(
            text="Risk Energy Evolution Over Time",
            font=dict(size=16, color="white")
        ),
        xaxis=dict(
            title="Timestep",
            gridcolor="#1A1E2E",
            color="white",
            range=[0, 28]
        ),
        yaxis=dict(
            title="Risk Energy (RE)",
            gridcolor="#1A1E2E",
            color="white",
            range=[0, 105]
        ),
        legend=dict(
            bgcolor="#1A1E2E",
            bordercolor="#333",
            borderwidth=1,
            font=dict(size=9)
        ),
        hovermode="x unified",
        height=420,
        margin=dict(l=40, r=40, t=50, b=40)
    )

    return fig
