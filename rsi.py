import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

st.set_page_config(page_title="Live RSI Strategy", layout="wide")

st.title("📊 Live RSI Strategy Dashboard (NSE)")

# Sidebar options
symbol = st.sidebar.selectbox("Select Stock", ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"])
interval = st.sidebar.selectbox("Select Interval", ["1m", "5m", "15m", "1h", "1d"])
period = st.sidebar.selectbox("Select Lookback Period", ["1d", "5d", "1mo"])
rsi_period = st.sidebar.slider("RSI Period", 5, 30, 14)

# Fetch data
@st.cache_data(ttl=300)
def fetch_data(symbol, interval, period):
    df = yf.download(tickers=symbol, interval=interval, period=period, progress=False)
    df.dropna(inplace=True)
    return df

df = fetch_data(symbol, interval, period)

# RSI calculation
#df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=rsi_period).rsi()
# Ensure 'Close' is valid Series
if 'Close' in df.columns:
    if df['Close'].notnull().any():
        close_prices = df['Close'].astype(float)
        rsi_calc = ta.momentum.RSIIndicator(close=close_prices, window=rsi_period)
        df['RSI'] = rsi_calc.rsi()
    else:
        st.error("Close price column contains only null values.")
        st.stop()
else:
    st.error("'Close' column not found in data.")
    st.stop()

    

# Last RSI and Signal
latest_rsi = df['RSI'].iloc[-1]
last_price = df['Close'].iloc[-1]

# Strategy Signal
if latest_rsi < 30:
    signal = "🟢 BUY"
elif latest_rsi > 70:
    signal = "🔴 SELL"
else:
    signal = "⚪ HOLD"

# Display Results
st.metric("📈 Last Price", f"₹{round(last_price, 2)}")
st.metric(f"📉 RSI ({rsi_period})", f"{round(latest_rsi, 2)}")
st.subheader(f"Strategy Signal: {signal}")

# Plot RSI + Price
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candles"))
fig.update_layout(title=f"{symbol} Price Chart", xaxis_rangeslider_visible=False)
st.plotly_chart(fig, use_container_width=True)

st.line_chart(df[['RSI']])
