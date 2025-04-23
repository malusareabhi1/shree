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

st.subheader("📈 Price vs EMA20")
st.line_chart(df[["Close", "EMA20"]])

# ─── STRATEGY TEST STOPPED ────────────────────────────────────────────────────
stop_msg = "🔴 Strategy Test Ended (for current run)"
st.info(stop_msg)
send_telegram(stop_msg)

# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
st.markdown("⏱️ Auto-refresh every 60 seconds")
with st.spinner("⏳ Refreshing in 30 seconds..."):
    time.sleep(30)
    st.rerun()
