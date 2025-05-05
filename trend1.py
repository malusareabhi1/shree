import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NIFTY Trend Viewer", layout="wide")
st.title("📊 NIFTY Multi-Timeframe Trend Analysis")

symbol = "^NSEI"

# Timeframes
timeframes = {
    "5-Min": {"interval": "5m", "period": "1d"},
    "1-Day": {"interval": "1d", "period": "30d"},
    "1-Week": {"interval": "1wk", "period": "1y"},
    "1-Month": {"interval": "1mo", "period": "5y"},
}

# Trend Calculation
def get_trend(df):
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    if df["EMA5"].iloc[-1] > df["EMA20"].iloc[-1]:
        return "🔼 Uptrend"
    elif df["EMA5"].iloc[-1] < df["EMA20"].iloc[-1]:
        return "🔻 Downtrend"
    else:
        return "➡️ Sideways"

# Calculate trend, price, high, low
def calculate_trend_for_timeframe(interval, period):
    try:
        df = yf.download(symbol, interval=interval, period=period, progress=False)
        df.dropna(inplace=True)
        if df.empty:
            return "No Data", 0, 0, 0
        trend = get_trend(df)
        current_price = float(df["Close"].iloc[-1])
        high = float(df["High"].max())
        low = float(df["Low"].min())
        return trend, current_price, high, low
    except Exception as e:
        return f"Error: {str(e)}", 0, 0, 0

# Display in Streamlit
for label, tf in timeframes.items():
    st.subheader(f"🕒 {label} Trend")
    trend, price, high, low = calculate_trend_for_timeframe(tf["interval"], tf["period"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📈 Trend", trend)
    col2.metric("💰 Price", f"{price:.2f} ₹")
    col3.metric("🔺 High", f"{high:.2f} ₹")
    col4.metric("🔻 Low", f"{low:.2f} ₹")
    st.divider()

import time

# Refresh every 30 seconds
st.write("🔄 Auto-refreshing in 30 seconds...")
time.sleep(30)
st.experimental_rerun()

    
    


