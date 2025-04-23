import os
import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
from datetime import datetime

# ───── CONFIG ───────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID       = os.getenv("TELEGRAM_CHAT_ID")

symbol   = "^NSEI"   # NIFTY index ticker
interval = "5m"      # 5-minute bars
period   = "5d"      # last 5 days

# ───── TELEGRAM ALERT ────────────────────────────────────────────────────
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except:
        st.error("⚠️ Telegram send failed")

# ───── DATA FETCH & CLEAN ────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_data(ticker: str) -> pd.DataFrame:
    df = yf.download(ticker, interval="5m", period="5d", progress=False)
    df.index = pd.to_datetime(df.index)

    # — Only localize if tz-naive; otherwise just convert —
    if df.index.tz is None:
        df = df.tz_localize("UTC").tz_convert("Asia/Kolkata")
    else:
        df = df.tz_convert("Asia/Kolkata")
    
    # Restrict to market hours
    df = df.between_time("09:15", "15:30")

    # Flatten MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Indicators
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["VMA20"] = df["Volume"].rolling(20).mean()

    return df

# ───── STREAMLIT UI ───────────────────────────────────────────────────────
st.set_page_config(page_title="📈 Nifty Live Breakout", layout="wide")
st.title("📊 Nifty 5-min EMA20+Volume Breakout Monitor")

data = fetch_data(symbol)
st.subheader(f"Latest Bars ({symbol})")
st.dataframe(data.tail(5))

# ───── STRATEGY LOGIC ────────────────────────────────────────────────────
signal = "No Signal"
if len(data) >= 2:
    prev   = data.iloc[-2]
    latest = data.iloc[-1]

    prev_c   = prev["Close"]
    prev_e   = prev["EMA20"]
    latest_c = latest["Close"]
    latest_v = latest["Volume"]
    latest_vma = latest["VMA20"]

    if (prev_c < prev_e) and (latest_c > prev_e) and (latest_v > latest_vma):
        signal = "BUY"
        entry = round(latest_c,2)
        msg = (
            f"📥 <b>LIVE BUY SIGNAL</b>\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Entry:</b> ₹{entry}\n"
            f"<b>V:</b> {latest_v:,}\n"
            f"<b>Time:</b> {latest.name.strftime('%H:%M')}"
        )
        send_telegram(msg)

# ───── DISPLAY METRICS & CHART ───────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Close", f"₹{latest['Close']:.2f}")
col2.metric("EMA20", f"₹{latest['EMA20']:.2f}")
col3.metric("Signal", signal)

st.subheader("Close & EMA20 Chart")
st.line_chart(data[["Close","EMA20"]])

# ───── AUTO-REFRESH ───────────────────────────────────────────────────────
st.markdown("⏱️ Auto-refresh every 60 seconds")
time.sleep(60)
st.experimental_rerun()
