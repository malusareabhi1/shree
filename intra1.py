import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.trend import EMAIndicator

st.set_page_config(layout="wide")
st.title("📈 Intraday Breakout Strategy (Simulated Live)")

symbol = st.text_input("Enter NSE Symbol (e.g., RELIANCE.NS)", "RELIANCE.NS")
interval = "5m"
period = "1d"

@st.cache_data(ttl=60)
def get_intraday_data(symbol):
    df = yf.download(symbol, interval=interval, period=period, progress=False)
    if df.empty or "Close" not in df.columns:
        return pd.DataFrame()
    return df

df = get_intraday_data(symbol)

if df.empty:
    st.error("No data received. Please check symbol or wait for market to open.")
    st.stop()

# Calculate indicators only if enough data is available
if len(df) < 20:
    st.warning("Not enough candles for 20 EMA. Try after 10:15 AM.")
    st.stop()

# Indicators
df["20EMA"] = EMAIndicator(df["Close"], window=20).ema_indicator()
df["VolumeAvg"] = df["Volume"].rolling(window=5).mean()

# Opening range: 9:15 - 9:30 (first 3 candles)
opening_range = df.iloc[0:3]
open_high = opening_range["High"].max()
open_low = opening_range["Low"].min()

latest = df.iloc[-1]
price = latest["Close"]
volume = latest["Volume"]
vol_avg = latest["VolumeAvg"]
ema20 = latest["20EMA"]

# Signal logic
signal = "🟡 No Trade"
if price > open_high and price > ema20 and volume > vol_avg:
    signal = "📈 BUY SIGNAL"
elif price < open_low and price < ema20 and volume > vol_avg:
    signal = "📉 SELL SIGNAL"

# Show metrics
col1, col2, col3 = st.columns(3)
col1.metric("Price", round(price, 2))
col2.metric("Volume", f"{int(volume):,}")
col3.metric("Signal", signal)

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"],
    low=df["Low"], close=df["Close"], name="Candles"
))
fig.add_trace(go.Scatter(
    x=df.index, y=df["20EMA"], mode="lines", name="20 EMA",
    line=dict(color="blue", width=1)
))
fig.add_hline(y=open_high, line=dict(color="green", dash="dash"), name="Opening High")
fig.add_hline(y=open_low, line=dict(color="red", dash="dash"), name="Opening Low")

fig.update_layout(height=600, width=1000, title=f"{symbol} - Intraday Strategy")
st.plotly_chart(fig, use_container_width=True)

st.caption("Auto-refresh every 1 min. Strategy: Opening Range Breakout + EMA + Volume Spike")
