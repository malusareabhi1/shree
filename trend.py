import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
from streamlit_autorefresh import st_autorefresh


st.set_page_config(layout="wide")
st.title("📊 NIFTY 50 Trend Checker")

nifty_50_symbols = [
    "ADANIENT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBIN.NS",
    "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TCS.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
]

@st.cache_data

def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        return df
    except:
        return None

def determine_trend(df):
    if df is None or len(df) < 50:
        return "Insufficient Data"
    last_row = df.iloc[-1]
    if float(last_row['SMA20']) > float(last_row['SMA50']):
        return "Uptrend"
    elif float(last_row['SMA20']) < float(last_row['SMA50']):
        return "Downtrend"
    else:
        return "Sideways"

st.info("Scanning NIFTY 50 stocks for trend using SMA20 vs SMA50...")

trend_data = []

for symbol in nifty_50_symbols:
    df = fetch_data(symbol)
    if df is not None and not df.empty:
        trend = determine_trend(df)
        last_close = float(df['Close'].iloc[-1])
        prev_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else last_close
        change_pct = ((last_close - prev_close) / prev_close) * 100 if prev_close != 0 else 0
        volume = int(df['Volume'].iloc[-1])
        trend_data.append({
            "Symbol": symbol.replace(".NS", ""),
            "Price": round(last_close, 2),
            "Change %": round(change_pct, 2),
            "Volume": volume,
            "Trend": trend
        })
    else:
        trend_data.append({
            "Symbol": symbol.replace(".NS", ""),
            "Price": None,
            "Change %": None,
            "Volume": None,
            "Trend": "No Data"
        })

df_trend = pd.DataFrame(trend_data)

# Display with colored highlighting
st.markdown("### 📈 Trend Overview")
def color_trend(val):
    color = "green" if val == "Uptrend" else ("red" if val == "Downtrend" else "gray")
    return f"color: {color}; font-weight: bold"

st.dataframe(
    df_trend.style.applymap(color_trend, subset=['Trend']),
    use_container_width=True
)

time.sleep(1)
#st.experimental_rerun()
st_autorefresh(interval=1000, limit=None, key="trendrefresh")
