import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import time

st.set_page_config(page_title="Nifty Live Strategy Monitor", layout="wide")

# Title and Status
st.title("📊 Nifty Live Algo Strategy")
st.markdown("Monitoring real-time breakout signals based on EMA20 and Volume")

# Parameters
symbol = "^NSEI"  # Nifty Index
interval = "5m"
period = "2d"

# Fetch Live Data
def fetch_data():
    df = yf.download(tickers=symbol, interval=interval, period=period, progress=False)
    df.dropna(inplace=True)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VMA20'] = df['Volume'].rolling(window=20).mean()
    return df

# Apply Strategy Logic
def apply_strategy(df):
    if len(df) < 2:
        st.warning("📉 Not enough data to evaluate strategy.")
        return

    prev = df.iloc[-2]
    latest = df.iloc[-1]

    # Extract values
    prev_close = float(prev['Close'])
    prev_ema20 = float(prev['EMA20'])
    latest_close = float(latest['Close'])
    latest_ema20 = float(latest['EMA20'])
    latest_volume = float(latest['Volume'])
    latest_vma20 = float(latest['VMA20'])

    # Apply breakout strategy
    if prev_close < prev_ema20 and latest_close > latest_ema20 and latest_volume > latest_vma20:
        st.success("✅ Entry Signal: Bullish Breakout Detected")
    else:
        st.info("🕒 No entry signal at the moment.")

# Main App
with st.spinner("Fetching live data..."):
    data = fetch_data()
    st.write(f"Latest Data Time: {data.index[-1]}")
    apply_strategy(data)
    st.line_chart(data[['Close', 'EMA20']])

# Refresh every 1 minute
st.markdown("⏱️ Refreshing every 1 minute...")
time.sleep(60)
st.experimental_rerun()
