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
