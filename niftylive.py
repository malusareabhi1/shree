import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

st.set_page_config(page_title="📈 Nifty Live EMA20", layout="wide")
st.title("📊 Nifty Live EMA20 Strategy Monitor")

symbol = "^NSEI"  # NIFTY index ticker
interval = "5m"   # 5-minute bars
period = "2d"     # last 2 days of data

@st.cache_data(ttl=60)  # cache data for 60s
def fetch_and_clean(ticker):
    df = yf.download(ticker, interval=interval, period=period, progress=False)
    
    # -- FLATTEN COLUMNS: drop any second-level (the ticker) --
    # If your df.columns is a MultiIndex, this will grab only level-0 names.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Now df.columns are ['Open','High','Low','Close','Adj Close','Volume'], etc.
    # Compute EMA20 on the 'Close' column
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    return df

# Fetch and display data
data = fetch_and_clean(symbol)

st.subheader("Latest data snapshot")
st.dataframe(data.tail(5))

# Plot Close vs EMA20 if available
if "Close" in data.columns and "EMA20" in data.columns:
    st.subheader("Close vs. EMA20")
    st.line_chart(data[["Close", "EMA20"]])
else:
    st.error("Required columns missing! Got:\n" + ", ".join(data.columns))

# Show timestamp of latest bar
latest_ts = data.index[-1].strftime("%Y-%m-%d %H:%M")
st.markdown(f"**Latest Bar:** {latest_ts}")

# Auto-refresh every 60 seconds
with st.spinner("Auto-refreshing in 60s..."):
    time.sleep(60)
    st.experimental_rerun()
