import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="NIFTY 15-Min Chart", layout="wide")
st.title("📈 NIFTY 15-Min Chart – Last 60 Days")

with st.spinner("Fetching NIFTY 15-min data..."):
    ticker = "^NSEI"  # Yahoo Finance code for NIFTY 50 index
    df = yf.download(ticker, interval="15m", period="60d", progress=False)
    df.reset_index(inplace=True)

# Convert UTC to IST
#df['Datetime'] = df['Datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
# Show table
st.subheader("📋 Data Preview")
st.dataframe(df.tail(50))

# Plot candlestick chart
st.subheader("🕯️ Candlestick Chart")
fig = go.Figure(data=[go.Candlestick(
    x=df['Datetime'],
    open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'],
    name='NIFTY'
)])

fig.update_layout(
    title="NIFTY 15-Min Candlestick Chart (Last 60 Days)",
    xaxis_title="DateTime (IST)",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)


