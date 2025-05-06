import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# Sidebar for Stock Selection
st.sidebar.title("📈 Stock Chart Dashboard")
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., BHARTIARTL.NS):", "BHARTIARTL.NS").upper()
start_date = st.sidebar.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=180))
end_date = st.sidebar.date_input("End Date", datetime.date.today())

# Fetch Data
df = yf.download(symbol, start=start_date, end=end_date)
if df.empty:
    st.error("No data available for this symbol or date range.")
    st.stop()

# Indicators
df['20_SMA'] = df['Close'].rolling(window=20).mean()
df['BB_upper'] = df['20_SMA'] + 2 * df['Close'].rolling(window=20).std()
df['BB_lower'] = df['20_SMA'] - 2 * df['Close'].rolling(window=20).std()
df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(14).mean() / df['Close'].pct_change().rolling(14).std()))

# Candlestick Chart
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Candlestick'
))

fig.add_trace(go.Scatter(
    x=df.index, y=df['20_SMA'], line=dict(color='orange'), name='20 SMA'
))

fig.add_trace(go.Scatter(
    x=df.index, y=df['BB_upper'], line=dict(color='lightblue'), name='BB Upper', opacity=0.5
))
fig.add_trace(go.Scatter(
    x=df.index, y=df['BB_lower'], line=dict(color='lightblue'), name='BB Lower', opacity=0.5
))

# Layout
fig.update_layout(
    title=f"{symbol} Price Chart with Bollinger Bands and 20-SMA",
    xaxis_title="Date",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# RSI Plot
st.subheader("📉 RSI Indicator")
rsi_fig = go.Figure()
rsi_fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI'))
rsi_fig.update_layout(yaxis=dict(range=[0, 100]), height=300)
st.plotly_chart(rsi_fig, use_container_width=True)
