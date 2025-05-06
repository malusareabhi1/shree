import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# Sidebar Inputs
st.sidebar.title("📊 TradingView-style Stock Dashboard")
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g., BHARTIARTL.NS):", "BHARTIARTL.NS").upper()
start_date = st.sidebar.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=180))
end_date = st.sidebar.date_input("End Date", datetime.date.today())

# Fetch data
df = yf.download(symbol, start=start_date, end=end_date)

if df.empty:
    st.error("No data found. Please check symbol or date.")
    st.stop()

# Technical Indicators
df['20_SMA'] = df['Close'].rolling(window=20).mean()
df['BB_std'] = df['Close'].rolling(window=20).std()
df['BB_upper'] = df['20_SMA'] + 2 * df['BB_std']
df['BB_lower'] = df['20_SMA'] - 2 * df['BB_std']

# RSI Calculation
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
df['RSI'] = 100 - (100 / (1 + rs))

# Drop NaNs from indicators
df.dropna(inplace=True)

# Plot Candlestick with Bollinger Bands
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
    name='Candlestick'
))
fig.add_trace(go.Scatter(x=df.index, y=df['20_SMA'], name='20 SMA', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='lightblue')))

fig.update_layout(title=f"{symbol} Price Chart", xaxis_title='Date', yaxis_title='Price', xaxis_rangeslider_visible=False, height=700)
st.plotly_chart(fig, use_container_width=True)

# RSI Plot
st.subheader("📉 RSI Indicator")
rsi_fig = go.Figure()
rsi_fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI'))
rsi_fig.update_layout(yaxis=dict(range=[0, 100]), height=300)
st.plotly_chart(rsi_fig, use_container_width=True)
