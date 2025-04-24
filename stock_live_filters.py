import os
import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─── LOAD ENVIRONMENT VARIABLES ───────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ─── TELEGRAM ALERT FUNCTION ──────────────────────────────────────────────────
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="📈 Nifty EMA20 Breakout", layout="wide")
st.title("📊 Nifty 5-min EMA20 + Volume Breakout Monitor")

# ─── STRATEGY TEST STARTED ─────────────────────────────────────────────────────
start_msg = "🟢 Strategy Test Started"
st.info(start_msg)
send_telegram(start_msg)

# ─── FETCH DATA ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_data(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, interval="5m", period="5d", progress=False)
    df.index = pd.to_datetime(df.index)

    if df.index.tz is None:
        df = df.tz_localize("UTC").tz_convert("Asia/Kolkata")
    else:
        df = df.tz_convert("Asia/Kolkata")

    df = df.between_time("09:15", "15:30")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["VMA20"] = df["Volume"].rolling(20).mean()
    return df

symbol = "^NSEI"
df = fetch_data(symbol)
latest = df.iloc[-1]
prev = df.iloc[-2]

# ─── MARKET OPEN/CLOSE MESSAGE ────────────────────────────────────────────────
now = latest.name
if now.hour == 9 and now.minute == 15:
    market_msg = "📈 Market Opened at 09:15"
    st.success(market_msg)
    send_telegram(market_msg)

if now.hour == 15 and now.minute == 30:
    market_close_msg = "📉 Market Closed at 15:30"
    st.warning(market_close_msg)
    send_telegram(market_close_msg)

# ─── STRATEGY LOGIC ───────────────────────────────────────────────────────────
signal = "No Signal"
if (prev["Close"] < prev["EMA20"]) and (latest["Close"] > prev["EMA20"]) and (latest["Volume"] > latest["VMA20"]):
    signal = "BUY"
    entry_price = round(latest["Close"], 2)
    msg = (
        f"📥 <b>LIVE BUY SIGNAL</b>\n"
        f"<b>Symbol:</b> {symbol}\n"
        f"<b>Entry:</b> ₹{entry_price}\n"
        f"<b>Volume:</b> {latest['Volume']:,}\n"
        f"<b>Time:</b> {latest.name.strftime('%H:%M')}"
    )
    send_telegram(msg)

# ─── DISPLAY ──────────────────────────────────────────────────────────────────
st.subheader("📊 Last 5 Candles")
st.dataframe(df.tail(5))

col1, col2, col3 = st.columns(3)
col1.metric("🔹 Close", f"₹{latest['Close']:.2f}")
col2.metric("🔸 EMA20", f"₹{latest['EMA20']:.2f}")
col3.metric("📌 Signal", signal)
#---------------------------------------------------------------------------------------
import plotly.graph_objects as go
from datetime import datetime

# ─── filter for today's date ──────────────────────────────────────
# assume df.index is timezone-aware in IST
today = datetime.now().astimezone(df.index.tz).date()
df_today = df[df.index.date == today]

# Calculate 20 EMA
df_today['EMA20'] = df_today['Close'].ewm(span=20, adjust=False).mean()

st.subheader("🕯️ Today's 5-Min Candle Chart with 20 EMA")

# Plot the candlestick chart with 20 EMA
fig = go.Figure(data=[
    go.Candlestick(
        x=df_today.index,
        open=df_today["Open"],
        high=df_today["High"],
        low=df_today["Low"],
        close=df_today["Close"],
        increasing_line_color="green",
        decreasing_line_color="red",
        name="Candles"
    ),
    go.Scatter(
        x=df_today.index,
        y=df_today['EMA20'],
        mode='lines',
        line=dict(color='blue', width=2),
        name='20 EMA'
    )
])

fig.update_layout(
    xaxis_rangeslider_visible=False,
    xaxis_title="Time",
    yaxis_title="Price (₹)",
    template="plotly_dark",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

#---------------------------------------------------------------------------------------
st.subheader("📈 Price vs EMA20")
st.line_chart(df[["Close", "EMA20"]])

# ─── STRATEGY TEST STOPPED ────────────────────────────────────────────────────
stop_msg = "🔴 Strategy Test Ended (for current run)"
st.info(stop_msg)
send_telegram(stop_msg)

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
st.markdown("⏱️ Auto-refresh every 30 seconds")
with st.spinner("⏳ Refreshing in 30 seconds..."):
    time.sleep(30)
    st.rerun()

#import datetime
#import streamlit as st

# Sidebar controls
chart_type = st.sidebar.selectbox("Select Chart Type", ["Candlestick", "Line", "OHLC"])
initial_capital = st.sidebar.number_input("Initial Capital (₹)", min_value=1000, value=100000, step=1000)
daily_trade_limit = st.sidebar.number_input("Daily Trade Limit", min_value=1, value=5)
start_time = st.sidebar.time_input("Trade Start Time", value=datetime.time(9, 30))
stop_time = st.sidebar.time_input("Trade Stop Time", value=datetime.time(14, 30))
lot_qty = st.sidebar.number_input("Lot Quantity", min_value=1, value=1)
stock = st.sidebar.selectbox("Select Stock", ["RELIANCE", "INFY", "HDFCBANK", "TCS", "ICICIBANK", "NIFTY", "BANKNIFTY"])
frame_interval = st.sidebar.selectbox("Select Time Frame", ["5m", "15m", "1h", "1d"])
order_type = st.sidebar.selectbox("Order Type", ["Market", "Limit"])

stop_loss_pct = st.sidebar.slider("Stop Loss (%)", min_value=0.5, max_value=10.0, value=1.0) / 100
profit_target_pct = st.sidebar.slider("Profit Target (%)", min_value=0.5, max_value=10.0, value=2.0) / 100
trailing_stop_pct = st.sidebar.slider("Trailing Stop Loss (%)", min_value=0.1, max_value=5.0, value=0.5) / 100
enable_time_exit = st.sidebar.checkbox("Enable Time-Based Exit", value=True)
exit_minutes = st.sidebar.slider("Exit After (Minutes)", min_value=1, max_value=60, value=10)

run_strategy = st.button("🚀 Run Strategy")
