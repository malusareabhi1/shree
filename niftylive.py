import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="📈 Nifty Live EMA20", layout="wide")
st.title("📊 Nifty Live EMA20 Strategy Monitor")

symbol = "^NSEI"        # NIFTY index ticker
interval = "5m"         # 5-minute bars
period = "2d"           # last 2 days of data

@st.cache(ttl=60)  # cache for 60s so we don’t hammer yfinance
def fetch_and_clean(ticker):
    # 1) Download
    df = yf.download(ticker, interval=interval, period=period, progress=False)
    # 2) Flatten multiindex columns
    #    E.g. ('Close','') → 'Close',   ('Volume','') → 'Volume'
    df.columns = [
        col[0] if col[1] == '' else f"{col[0]}_{col[1]}"
        for col in df.columns.to_flat_index()
    ]
    # 3) If you had multiple tickers you’d handle suffixes here.
    # 4) Compute EMA20 on the cleaned 'Close' column
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    return df

# Fetch data
data = fetch_and_clean(symbol)

# Show last few rows
st.subheader("Latest data snapshot")
st.dataframe(data.tail(5))

# Plot only if columns exist
if "Close" in data.columns and "EMA20" in data.columns:
    st.subheader("Close vs. EMA20")
    st.line_chart(data[["Close", "EMA20"]])
else:
    st.error("Required columns missing! Got:\n" + ", ".join(data.columns))

# Optional: show timestamp of latest bar
latest_ts = data.index[-1].strftime("%Y-%m-%d %H:%M")
st.markdown(f"**Latest Bar:** {latest_ts}")

# Auto-refresh every 60 seconds
with st.spinner("Auto-refreshing in 60s..."):
    time.sleep(60)
    st.experimental_rerun()
