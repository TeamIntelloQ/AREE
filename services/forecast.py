import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

def forecast_re(current_re: list, horizon: int = 5) -> list:
    """Predict next N steps from history"""
    X = np.arange(len(current_re)).reshape(-1, 1)
    y = np.array(current_re)
    
    model = LinearRegression().fit(X, y)
    future = np.arange(len(current_re), len(current_re) + horizon).reshape(-1, 1)
    
    predictions = model.predict(future).tolist()
    return [max(0, min(1.0, p)) for p in predictions]

# Test
history = [0.1, 0.25, 0.4, 0.65, 0.82]  # Rising RE
future = forecast_re(history)
print(f"Future RE: {future}")
