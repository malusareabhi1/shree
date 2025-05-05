import streamlit as st
import yfinance as yf
import pandas as pd
from ta.trend import EMAIndicator

st.set_page_config(page_title="Nifty/BankNifty Trend", layout="wide")
st.title("📈 Nifty / BankNifty Trend Analyzer")

# Sidebar
symbol = st.sidebar.selectbox("Select Index", ("^NSEI", "^NSEBANK"))  # Nifty / Bank Nifty
timeframe = st.sidebar.selectbox("Select Timeframe", ("Intraday (5 min)", "Daily", "Weekly", "Monthly"))

# Map intervals
interval_map = {
    "Intraday (5 min)": ("5m", "2d"),
    "Daily": ("1d", "3mo"),
    "Weekly": ("1d", "6mo"),
    "Monthly": ("1d", "1y")
}

interval, period = interval_map[timeframe]

# Fetch data
@st.cache_data
def get_data(symbol, interval, period):
    try:
        df = yf.download(tickers=symbol, interval=interval, period=period)
        return df
    except Exception as e:
        st.error(f"Data load failed: {e}")
        return pd.DataFrame()

df = get_data(symbol, interval, period)

# Exit if data load failed
if df.empty:
    st.error("Failed to load data. Check internet or symbol.")
    st.stop()

# Resample if Weekly/Monthly
if "Weekly" in timeframe:
    df = df.resample("W").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})
elif "Monthly" in timeframe:
    df = df.resample("M").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"})

# Drop missing
df.dropna(inplace=True)

# Add EMA
df["EMA20"] = EMAIndicator(close=df["Close"], window=20).ema_indicator()
df["EMA50"] = EMAIndicator(close=df["Close"], window=50).ema_indicator()

# Get latest values
latest = df.iloc[-1]
current_price = latest["Close"]
ema20 = latest["EMA20"]
ema50 = latest["EMA50"]

# Check valid values
if pd.isna(current_price) or pd.isna(ema20) or pd.isna(ema50):
    st.error("Insufficient data to determine trend.")
    st.dataframe(df.tail())
else:
    # Determine trend
    if ema20 > ema50:
        st.success("📈 Current Trend: UP")
    else:
        st.error("📉 Current Trend: DOWN")

    # Metrics
    st.metric("Latest Close", f"{current_price:.2f}")
    st.metric("EMA 20", f"{ema20:.2f}")
    st.metric("EMA 50", f"{ema50:.2f}")

    # Chart
    st.line_chart(df[["Close", "EMA20", "EMA50"]])
