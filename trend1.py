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
# Ensure 'Close' column is clean
df = df[pd.to_numeric(df['Close'], errors='coerce').notnull()]
df['Close'] = pd.to_numeric(df['Close'])

# Drop NA to avoid indicator crash
df.dropna(subset=["Close"], inplace=True)

# Only calculate EMA if enough rows
if len(df) >= 50:
    df["EMA20"] = EMAIndicator(close=df["Close"], window=20).ema_indicator()
    df["EMA50"] = EMAIndicator(close=df["Close"], window=50).ema_indicator()

    latest = df.iloc[-1]
    current_price = latest["Close"]
    ema20 = latest["EMA20"]
    ema50 = latest["EMA50"]

    # Trend Logic
    if pd.notna(ema20) and pd.notna(ema50):
        if ema20 > ema50:
            st.success("📈 Current Trend: UP")
        else:
            st.error("📉 Current Trend: DOWN")

        # Show Metrics
        st.metric("Latest Close", f"{current_price:.2f}")
        st.metric("EMA 20", f"{ema20:.2f}")
        st.metric("EMA 50", f"{ema50:.2f}")

        # Chart
        st.line_chart(df[["Close", "EMA20", "EMA50"]])
    else:
        st.warning("EMA values could not be computed. Try a longer date range.")
else:
    st.warning("Not enough data to compute EMA (need at least 50 rows).")
