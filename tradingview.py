import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

st.set_page_config(layout="wide")
st.title("📊 NSE Stock Dashboard - TradingView Style")

# ---------------------------------------
# 🏷️ Input
symbol = st.text_input("Enter NSE Symbol (e.g., RELIANCE, TCS, BHARTIARTL)", "BHARTIARTL").upper()
full_symbol = symbol + ".NS"
start_date = st.date_input("Start Date", datetime.date(2023, 1, 1))
end_date = datetime.date.today()

# ---------------------------------------
# 📥 Download Data
df = yf.download(full_symbol, start=start_date, end=end_date)

if df.empty:
    st.warning("No data found for this symbol.")
    st.stop()

# ---------------------------------------
# 📈 Indicators
# Bollinger Bands
df["20_SMA"] = df["Close"].rolling(window=20).mean()
df["BB_upper"] = df["20_SMA"] + 2 * df["Close"].rolling(window=20).std()
df["BB_lower"] = df["20_SMA"] - 2 * df["Close"].rolling(window=20).std()

# RSI
delta = df["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
df["RSI"] = 100 - (100 / (1 + rs))

# ---------------------------------------
# 📊 Main Chart (Candlestick + BB + Volume)
fig = go.Figure()

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Candles"
))

# Bollinger Bands
fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper", line=dict(color="red", width=1)))
fig.add_trace(go.Scatter(x=df.index, y=df["20_SMA"], name="20 SMA", line=dict(color="blue", width=1)))
fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower", line=dict(color="green", width=1)))

# Volume Bars
fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="rgba(100, 100, 255, 0.4)", yaxis='y2'))

fig.update_layout(
    title=f"{symbol} - Daily Candlestick with Bollinger Bands",
    xaxis_rangeslider_visible=False,
    yaxis=dict(title="Price"),
    yaxis2=dict(overlaying='y', side='right', title="Volume", showgrid=False),
    legend=dict(orientation="h")
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------
# RSI Chart
rsi_fig = go.Figure()
rsi_fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)", line=dict(color="purple")))
rsi_fig.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=70, y1=70, line=dict(dash='dash', color="red"))
rsi_fig.add_shape(type='line', x0=df.index[0], x1=df.index[-1], y0=30, y1=30, line=dict(dash='dash', color="green"))
rsi_fig.update_layout(title="Relative Strength Index (RSI)", yaxis=dict(range=[0, 100]))
st.plotly_chart(rsi_fig, use_container_width=True)
