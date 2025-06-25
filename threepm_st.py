import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY 15-Min Chart", layout="wide")
st.title("📈 NIFTY 15-Min Chart – Last 60 Days")

with st.spinner("Fetching NIFTY 15-min data..."):
    ticker = "^NSEI"
    df = yf.download(ticker, interval="15m", period="60d", progress=False)

    # Reset index to move Datetime from index to column
    df.reset_index(inplace=True)

    # Get actual datetime column name after reset
    datetime_col = df.columns[0]

    # Convert to datetime and then IST
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df[datetime_col] = df[datetime_col].dt.tz_convert('Asia/Kolkata')

    # Rename to 'datetime' for consistency
    df = df.rename(columns={datetime_col: 'datetime'})

# Just in case yfinance gives multi-index columns, flatten them
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]

# Preview data
st.subheader("📋 Data Preview")
st.dataframe(df.tail(50))

# Candlestick chart
st.subheader("🕯️ NIFTY Candlestick Chart (15m)")

fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'],
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name="NIFTY"
)])

fig.update_layout(
    title="NIFTY 15-Min Chart (Last 60 Days)",
    xaxis_title="DateTime (IST)",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)
