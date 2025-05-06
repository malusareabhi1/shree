import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.trend import EMAIndicator
from dotenv import load_dotenv
import time

st.set_page_config(layout="wide")
st.title("📈 Intraday Opening Range Breakout Strategy")

# Live Algo Trading Block
st.title("🤖 Live Algo Trading (Paper/Real Mode)")
st.title("📊 Live NIFTY 5‑Minute Candle")

# -------------------------------------------------------------------------------------------------
# Trend Calculation
def get_trend(df):
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    if df["EMA5"].iloc[-1] > df["EMA20"].iloc[-1]:
        return "🔼 Uptrend"
    elif df["EMA5"].iloc[-1] < df["EMA20"].iloc[-1]:
        return "🔻 Downtrend"
    else:
        return "➡️ Sideways"

# Fetch 5-minute data
def fetch_5min_data(symbol):
    df = yf.download(tickers=symbol, interval="5m", period="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("Asia/Kolkata")
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    return df

# Plot basic candlestick chart
def plot_candles(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
    )])
    fig.update_layout(
        title="NIFTY 5‑Minute Candles (Today)",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )
    return fig

# Plot candlestick chart with 20-SMA
def plot_candles_with_sma(df):
    df['20-SMA'] = df['Close'].rolling(window=20).mean()

    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candlesticks"
    )])

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['20-SMA'],
        mode='lines',
        name='20-SMA',
        line=dict(color='orange', width=2)
    ))

    fig.update_layout(
        title="NIFTY 5‑Minute Candles with 20-SMA (Today)",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )

    return fig

# -------------------------------------------------------------------------------------------------
# Main Execution
symbol = "^NSEI"
df = fetch_5min_data(symbol)

if df.empty:
    st.warning("No data available for today’s 5‑min bars.")
else:
    trend = get_trend(df)
    current_price = float(df["Close"].iloc[-1])
    high = float(df["High"].max())
    low = float(df["Low"].min())

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📈 Trend", trend)
    col2.metric("💰 Price", f"{current_price:.2f} ₹")
    col3.metric("🔺 High", f"{high:.2f} ₹")
    col4.metric("🔻 Low", f"{low:.2f} ₹")

    # Display candlestick chart with SMA
    st.plotly_chart(plot_candles_with_sma(df), use_container_width=True)
    st.divider()

    # Pause for refresh
    time.sleep(30)
