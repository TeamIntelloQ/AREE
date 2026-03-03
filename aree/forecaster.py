import numpy as np
from scipy.integrate import odeint

def dre_dt(re, t, alpha=0.12, beta=0.05, gamma=0.01):
    """
    RE dynamics equation:
    alpha = growth rate (threat pressure building)
    beta  = natural decay (system recovering)
    gamma = entropy dissipation (cooling effect)
    dRE/dt = alpha*RE - beta*RE - gamma*RE^2
    """
    re_val = re[0]
    drdt = alpha * re_val - beta * re_val - gamma * re_val**2
    return [drdt]

def forecast_re(initial_re, t_steps=10, dt=1.0):
    """Forecast how RE evolves over next t_steps time units"""
    t = np.linspace(0, t_steps * dt, t_steps)
    solution = odeint(dre_dt, [initial_re], t)
    return t.tolist(), solution.flatten().tolist()

def should_intervene(re_forecast, threshold=70):
    """Returns True if RE predicted to exceed threshold"""
    return any(re > threshold for re in re_forecast)

if __name__ == "__main__":
    t, forecast = forecast_re(initial_re=64.58, t_steps=15)
    print("=" * 40)
    print("  RE Forecast (15 steps):")
    for i, (time, re) in enumerate(zip(t, forecast)):
        bar = "█" * int(re / 5)
        print(f"  t={time:.1f} → RE={re:.2f} {bar}")
    print("=" * 40)
    print(f"  Intervene? {should_intervene(forecast)}")
    print("=" * 40)
