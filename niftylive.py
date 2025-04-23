import streamlit as st
import yfinance as yf
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import requests

st.set_page_config(page_title="📈 NIFTY Live Monitor", layout="wide")

# Auto-refresh every 60 seconds
st_autorefresh(interval=60 * 1000, key="refresh")

# Telegram Bot Function
def send_telegram(msg):
    token = 'YOUR_TELEGRAM_BOT_TOKEN'
    chat_id = 'YOUR_CHAT_ID'
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=payload)

# Sidebar
st.sidebar.title("NIFTY Live Strategy Monitor")
symbol = st.sidebar.selectbox("Choose NIFTY Stock", ["^NSEI","RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS"])
capital = st.sidebar.number_input("Capital (₹)", value=50000)
sl_percent = st.sidebar.slider("SL %", 0.5, 5.0, 1.5)

# Fetch Live Data
def get_live_data(ticker):
    df = yf.download(ticker, interval='5m', period='1d', progress=False)
    df.dropna(inplace=True)
    return df

df = get_live_data(symbol)

# Apply Strategy
df['EMA20'] = df['Close'].ewm(span=20).mean()
df['VMA20'] = df['Volume'].rolling(20).mean()

latest = df.iloc[-1]
prev = df.iloc[-2]

signal = None
entry = None
sl = None

prev_close = float(prev['Close'])
prev_ema = float(prev['EMA20'])
latest_close = float(latest['Close'])
latest_ema = float(latest['EMA20'])
latest_vol = float(latest['Volume'])
latest_vma = float(latest['VMA20'])

#if prev['Close'] < prev['EMA20'] and latest['Close'] > latest['EMA20'] and latest['Volume'] > latest['VMA20']:
if prev_close < prev_ema20 and latest_close > latest_ema20 and latest_volume > latest_vma20:
    # execute strategy    
    signal = "BUY"
    entry = round(latest['Close'], 2)
    sl = round(entry * (1 - sl_percent / 100), 2)
    qty = int(capital / entry)
    message = f"📥 <b>LIVE BUY SIGNAL</b>\nSymbol: {symbol}\nEntry: ₹{entry}\nSL: ₹{sl}\nQty: {qty}\nTime: {datetime.now().strftime('%H:%M:%S')}"
    send_telegram(message)
else:
    signal = "No Signal"

# Display
st.title(f"📊 Live Strategy Monitor: {symbol}")
st.metric("Current Price", round(latest['Close'], 2))
st.metric("Volume", int(latest['Volume']))
st.metric("Signal", signal)

st.line_chart(df[['Close', 'EMA20']])
st.bar_chart(df['Volume'])

with st.expander("🔍 Raw Data"):
    st.dataframe(df.tail(10))
