import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="NIFTY 15-Min Chart", layout="wide")
st.title("📈 NIFTY 15-Min Chart – Last 60 Days")

with st.spinner("Fetching NIFTY 15-min data..."):
    ticker = "^NSEI"
    df = yf.download(ticker, interval="15m", period="60d", progress=False)
    df.reset_index(inplace=True)

    # Detect datetime column
    datetime_col = df.columns[0]
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df[datetime_col] = df[datetime_col].dt.tz_convert('Asia/Kolkata')
    df = df.rename(columns={datetime_col: 'datetime'})

# Clean multi-index columns if any
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

# Preview table
st.subheader("📋 Data Preview")
st.dataframe(df.tail(50))

# Candlestick chart
st.subheader("🕯️ Candlestick Chart")
fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'],
    open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'],
    name='NIFTY'
)])

fig.update_layout(
    title="NIFTY 15-Min Candlestick Chart (Last 60 Days)",
    xaxis_title="Datetime (IST)",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)
