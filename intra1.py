import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.trend import EMAIndicator
st.set_page_config(layout="wide")
st.title("📈 Intraday Opening Range Breakout Strategy")

# User input
symbol = st.text_input("Enter NSE Stock Symbol (e.g., RELIANCE.NS)", "RELIANCE.NS")

@st.cache_data(ttl=60)
def get_intraday_data(symbol):
    df = yf.download(symbol, interval="5m", period="1d", progress=False)
    return df.dropna() if not df.empty else pd.DataFrame()

df = get_intraday_data(symbol)

if df.empty:
    st.error("❌ No data received. Check symbol or wait for market to open.")
    st.stop()
opening_range = df.iloc[0:3]
open_high = opening_range["High"].max()
open_low = opening_range["Low"].min()

# Drop NaNs and check for sufficient rows
if len(df) < 20:
    st.warning("Not enough data for 20 EMA. Try after 10:15 AM.")
    st.stop()

# 20 EMA
try:
    df["20EMA"] = EMAIndicator(df["Close"], window=20).ema_indicator()
    df["VolumeAvg"] = df["Volume"].rolling(window=5).mean()
except Exception as e:
    st.error(f"Indicator calculation error: {e}")
    st.stop()
