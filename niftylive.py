import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="NIFTY 50 Live Chart", layout="wide")

st.title("📈 NIFTY 50 Live Chart")

# Load NIFTY 50 Index
ticker = "^NSEI"

# Auto refresh toggle
refresh = st.checkbox("Auto-refresh every 60 seconds", value=True)

# Live price
nifty = yf.Ticker(ticker)
data = nifty.history(period="1d", interval="1m")
live_price = data["Close"].iloc[-1]

st.metric(label="NIFTY 50 Live Price", value=f"{live_price:.2f}")

# Plot chart
st.line_chart(data["Close"])

# Optional auto-refresh
if refresh:
    time.sleep(60)
    st.experimental_rerun()
