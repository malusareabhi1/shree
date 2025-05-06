import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.trend import EMAIndicator
from dotenv import load_dotenv
import time

st.set_page_config(layout="wide")
st.title("📈 Intraday Opening Range Breakout Strategy")
st.title("📊 Live 5‑Minute Candle Analysis")

# -------------------------------------------------------------------------------------------------
# Stock Selector
#default_symbol = "RELIANCE.NS"  # You can change this to any default
#symbol = st.text_input("Enter NSE Stock Symbol (e.g., RELIANCE.NS, TCS.NS, INFY.NS):", default_symbol).upper()
# NIFTY 50 Stock List
nifty50_stocks = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE",
    "BAJAJFINSV", "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
    "ICICIBANK", "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NTPC",
    "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM",
    "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "UPL", "ULTRACEMCO", "WIPRO"
]
selected_stock = st.selectbox("Select a NIFTY 50 Stock", sorted(nifty50_stocks))
symbol = selected_stock + ".NS"

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
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("Asia/Kolkata")
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    return df

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
        title=f"{symbol} 5‑Minute Candles with 20-SMA (Today)",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )
    return fig

# -------------------------------------------------------------------------------------------------
# Main Execution
df = fetch_5min_data(symbol)

if df.empty:
    st.warning(f"No data available for symbol: {symbol}")
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

    # Display candlestick chart
    st.plotly_chart(plot_candles_with_sma(df), use_container_width=True)
    st.divider()

    # Opening Range Breakout
    opening_range = df.between_time("09:15", "09:30")
    if len(opening_range) < 3:
        st.warning("Not enough data yet for Opening Range (need 3 candles).")
    else:
        or_high = opening_range["High"].max()
        or_low = opening_range["Low"].min()
        or_close_time = opening_range.index[-1]

        # Identify breakout after 9:30
        post_or = df[df.index > or_close_time]
        breakout_signal = ""
        for idx, row in post_or.iterrows():
            if row["Close"] > or_high and row["Volume"] > opening_range["Volume"].mean():
                breakout_signal = f"🔼 Long Signal at {idx.time()} (Price: {row['Close']:.2f})"
                break
            elif row["Close"] < or_low and row["Volume"] > opening_range["Volume"].mean():
                breakout_signal = f"🔽 Short Signal at {idx.time()} (Price: {row['Close']:.2f})"
                break

        st.subheader("📊 Opening Range Breakout (ORB)")
        st.write(f"Opening Range High: {or_high:.2f} | Low: {or_low:.2f}")
        st.success(breakout_signal if breakout_signal else "❌ No breakout detected yet.")

    time.sleep(30)
