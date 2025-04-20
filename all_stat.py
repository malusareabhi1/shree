import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm
import plotly.graph_objects as go

# --- Black-Scholes Formula ---
def black_scholes(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'call':
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'put':
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# --- Payoff Functions with Real Premiums ---
def payoff_straddle(S_range, S, K, T, r, sigma):
    call_premium = black_scholes(S, K, T, r, sigma, 'call')
    put_premium = black_scholes(S, K, T, r, sigma, 'put')
    return np.maximum(S_range - K, 0) + np.maximum(K - S_range, 0) - (call_premium + put_premium)

def payoff_strangle(S_range, S, K1, K2, T, r, sigma):
    call_premium = black_scholes(S, K2, T, r, sigma, 'call')
    put_premium = black_scholes(S, K1, T, r, sigma, 'put')
    return np.maximum(S_range - K2, 0) + np.maximum(K1 - S_range, 0) - (call_premium + put_premium)

def payoff_iron_condor(S_range, S, Kp1, Kp2, Kc1, Kc2, T, r, sigma):
    # Short Put Spread + Short Call Spread
    short_put = black_scholes(S, Kp1, T, r, sigma, 'put')
    long_put = black_scholes(S, Kp2, T, r, sigma, 'put')
    short_call = black_scholes(S, Kc1, T, r, sigma, 'call')
    long_call = black_scholes(S, Kc2, T, r, sigma, 'call')
    total_premium = short_put - long_put + short_call - long_call
    return (np.maximum(Kp1 - S_range, 0) - np.maximum(Kp2 - S_range, 0) +
            np.maximum(S_range - Kc1, 0) - np.maximum(S_range - Kc2, 0) + total_premium)

# --- Streamlit App ---
st.title("📊 Nifty Option Strategy Analytics - Real World Simulation")

# User inputs
strategy = st.sidebar.selectbox("Select Strategy", [
    "Straddle", "Strangle", "Iron Condor"
])

st.sidebar.markdown("---")
days_to_expiry = st.sidebar.slider("Days to Expiry", 1, 60, 30)
volatility = st.sidebar.slider("Implied Volatility (%)", 10, 50, 18) / 100
risk_free_rate = st.sidebar.number_input("Risk-Free Rate (%)", value=6.0) / 100
strike_interval = st.sidebar.slider("Strike Interval", 50, 500, 100, step=50)

# Fetch current Nifty price
nifty_data = yf.download("^NSEI", period="1d", interval="1m")
current_price = nifty_data['Close'].iloc[-1] if not nifty_data.empty else 19500
st.sidebar.write(f"📌 Current Nifty Price: ₹{current_price:.2f}")

# Define strike prices
K = round(current_price / strike_interval) * strike_interval
K1 = K - strike_interval
K2 = K + strike_interval
K3 = K + 2 * strike_interval
K0 = K - 2 * strike_interval

S_range = np.linspace(current_price * 0.8, current_price * 1.2, 300)
T = days_to_expiry / 365

# Strategy payoff
if strategy == "Straddle":
    payoff = payoff_straddle(S_range, current_price, K, T, risk_free_rate, volatility)
elif strategy == "Strangle":
    payoff = payoff_strangle(S_range, current_price, K1, K2, T, risk_free_rate, volatility)
elif strategy == "Iron Condor":
    payoff = payoff_iron_condor(S_range, current_price, K1, K0, K2, K3, T, risk_free_rate, volatility)
else:
    payoff = np.zeros_like(S_range)

# Plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=S_range, y=payoff, mode='lines', name=strategy))
fig.update_layout(title=f"{strategy} Strategy Payoff (with Real Premiums)",
                  xaxis_title="Nifty Spot Price at Expiry",
                  yaxis_title="Net Payoff (₹)",
                  xaxis_rangeslider_visible=True)

st.plotly_chart(fig, use_container_width=True)

# Show metrics
st.subheader("📈 Strategy Snapshot")
st.metric("Current Price", f"₹{current_price:.2f}")
st.metric("ATM Strike (K)", f"{K}")
st.metric("Implied Volatility", f"{volatility*100:.1f}%")
st.metric("Days to Expiry", f"{days_to_expiry} Days")
