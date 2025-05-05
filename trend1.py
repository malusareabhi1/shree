import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Index Trend Checker", layout="centered")

st.title("📈 Nifty / BankNifty Trend Checker")

# Select index
index_option = st.selectbox("Select Index", ["NIFTY 50", "BANKNIFTY"])

symbol_map = {
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}
symbol = symbol_map[index_option]

# Fetch data
df = yf.download(tickers=symbol, period="90d", interval="15m", progress=False)

if df.empty:
    st.error("Failed to load data. Please check internet connection or symbol.")
    st.stop()

# Calculate EMAs
df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

# Determine current trend
if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]:
    trend = "🔼 Uptrend"
    st.success(f"Current Trend: {trend}")
else:
    trend = "🔽 Downtrend"
    st.error(f"Current Trend: {trend}")

# Show last close price
st.metric("Current Price", f"{df['Close'].iloc[-1]:.2f}")

# Plot
st.subheader("Price & EMA Chart")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["Close"], label="Close", color="black")
ax.plot(df["EMA20"], label="EMA 20", color="blue", linestyle="--")
ax.plot(df["EMA50"], label="EMA 50", color="red", linestyle="--")
ax.set_title(f"{index_option} Trend (15-min interval)")
ax.set_xlabel("Time")
ax.set_ylabel("Price")
ax.legend()
st.pyplot(fig)
