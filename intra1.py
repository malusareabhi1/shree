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
    # Make sure df["Close"] is a 1D Series (not a 2D DataFrame)
    st.write(df["Close"].shape)  # Debugging step: print shape of 'Close'
    st.write("DataFrame info:", df.info())  # Check structure
    st.write("Shape of Close column:", df["Close"].shape)  # Ensure it's 1D
    
    # Ensure df["Close"] is a 1D Series, not a 2D DataFrame
    df["Close"] = df["Close"].squeeze()  # Convert to 1D Series if needed
    
    # Calculate EMA
    df["20EMA"] = EMAIndicator(close=df["Close"], window=20).ema_indicator()

    df["20EMA"] = EMAIndicator(df["Close"], window=20).ema_indicator()
    st.write(df["Close"].shape)  # Should print (N,) where N is the number of rows

    df["VolumeAvg"] = df["Volume"].rolling(window=5).mean()
except Exception as e:
    st.error(f"Indicator calculation error: {e}")
    st.stop()
latest = df.iloc[-1]
price = latest["Close"]
volume = latest["Volume"]
vol_avg = latest["VolumeAvg"]
ema = latest["20EMA"]

signal = "🟡 No Trade"
if price > open_high and price > ema and volume > vol_avg:
    signal = "📈 BUY SIGNAL"
elif price < open_low and price < ema and volume > vol_avg:
    signal = "📉 SELL SIGNAL"

col1, col2, col3 = st.columns(3)
col1.metric("Current Price", round(price, 2))
col2.metric("Volume", f"{int(volume):,}")
col3.metric("Signal", signal)

fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name="Candles"
))

# EMA line
fig.add_trace(go.Scatter(
    x=df.index, y=df["20EMA"], mode="lines",
    name="20 EMA", line=dict(color="blue")
))

# Opening range lines
fig.add_hline(y=open_high, line=dict(color="green", dash="dash"), name="Opening High")
fig.add_hline(y=open_low, line=dict(color="red", dash="dash"), name="Opening Low")

fig.update_layout(title=f"{symbol} - Intraday Chart", height=600)

st.plotly_chart(fig, use_container_width=True)
st.caption("Auto-refresh every 1 min. Strategy: Opening Range Breakout + EMA + Volume Spike")



