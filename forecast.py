# forecast.py — Risk Energy Forecasting
# Input:  list of past RE values (from re_computed.csv or live loop)
# Output: predicted future RE values

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


# ── ARIMA Forecast ────────────────────────────────────────────────────────────
def forecast_arima(re_history, steps=5):
    """
    Uses ARIMA(2,1,2) to predict next `steps` RE values.
    Falls back to moving average if ARIMA fails.
    re_history: list or array of floats (RE values over time)
    Returns: numpy array of predicted values
    """
    try:
        from statsmodels.tsa.arima.model import ARIMA
        if len(re_history) < 10:
            # Not enough data for ARIMA — use moving average
            return forecast_moving_average(re_history, steps)

        model  = ARIMA(re_history, order=(2, 1, 2))
        result = model.fit()
        future = result.forecast(steps=steps)
        return np.clip(future, 0, 100)

    except Exception as e:
        print(f"  ⚠ ARIMA failed ({e}), using moving average")
        return forecast_moving_average(re_history, steps)


# ── Moving Average Forecast (fallback) ───────────────────────────────────────
def forecast_moving_average(re_history, steps=5, window=5):
    """
    Simple moving average with trend extrapolation.
    """
    history = np.array(re_history)
    if len(history) < 2:
        return np.array([history[-1]] * steps)

    window  = min(window, len(history))
    ma      = np.mean(history[-window:])

    # Compute trend from last window
    if len(history) >= window:
        trend = (history[-1] - history[-window]) / window
    else:
        trend = 0.0

    future = [ma + trend * (i + 1) for i in range(steps)]
    return np.clip(future, 0, 100)


# ── Cascade Risk Flag ─────────────────────────────────────────────────────────
def check_cascade_risk(predicted_values, threshold=90.0):
    """
    Returns True if any predicted RE crosses the intervention threshold.
    """
    return any(v >= threshold for v in predicted_values)


# ── Per-Service Forecast ──────────────────────────────────────────────────────
def forecast_all_services(re_computed_csv="re_computed.csv", steps=5):
    """
    Loads re_computed.csv and forecasts future RE for each service.
    Prints summary and returns dict of {service: predicted_array}.
    """
    df       = pd.read_csv(re_computed_csv)
    services = df["service"].unique()
    forecasts = {}

    print("\n" + "="*55)
    print("  RISK ENERGY FORECAST  (+{} timesteps)".format(steps))
    print("="*55)

    for svc in services:
        history = df[df["service"] == svc].sort_values("t")["RE"].tolist()
        preds   = forecast_arima(history, steps=steps)
        forecasts[svc] = preds

        cascade = check_cascade_risk(preds)
        flag    = "🔴 CASCADE RISK" if cascade else "🟢 STABLE"
        print(f"  {svc:<22} current={history[-1]:.1f}  "
              f"predicted={[round(v,1) for v in preds]}  {flag}")

    print("="*55)
    return forecasts


# ── Run standalone ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    forecasts = forecast_all_services("re_computed.csv", steps=5)
