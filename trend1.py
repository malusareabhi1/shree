import streamlit as st
import yfinance as yf
import pandas as pd
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

# Download daily data
df = yf.download(tickers=symbol, period="90d", interval="1d", progress=False)

if df.empty:
    st.error("Failed to load data. Please check internet connection or try later.")
    st.stop()

# Calculate EMAs
df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

# Determine current trend
latest_ema20 = df["EMA20"].iloc[-1]
latest_ema50 = df["EMA50"].iloc[-1]
current_price = df["Close"].iloc[-1]

if latest_ema20 > latest_ema50:
    trend = "🔼 Uptrend"
    st.success(f"Current Trend: {trend}")
else:
    trend = "🔽 Downtrend"
    st.error(f"Current Trend: {trend}")

# Display current status
st.metric("Latest Close", f"{current_price:.2f}")
st.metric("EMA20", f"{latest_ema20:.2f}")
st.metric("EMA50", f"{latest_ema50:.2f}")

# Plot
st.subheader("Price & EMA Chart")
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df["Close"], label="Close", color="black")
ax.plot(df["EMA20"], label="EMA 20", color="blue", linestyle="--")
ax.plot(df["EMA50"], label="EMA 50", color="red", linestyle="--")
ax.set_title(f"{index_option} Trend (Daily)")
ax.set_xlabel("Date")
ax.set_ylabel("Price")
ax.legend()
st.pyplot(fig)
