import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import random
import requests
from kiteconnect import KiteConnect
import time
import threading
import datetime
from datetime import datetime, timedelta
import os
import pytz
import ta  # Required for trend calculation (ensure installed)


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Strategy Settings")

st.sidebar.title("📋 Navigation")
selected = st.sidebar.selectbox("Choose a section", [
    "Home",
    "Live Algo Trading",
    "Backtest Strategy",
    "View Logs",
    "Settings"
])

telegram_alert = st.sidebar.checkbox("📣 Send Telegram Alerts", value=True)

st.sidebar.markdown("---")
st.sidebar.success("🟢 Strategy Status: Active")
st.sidebar.markdown("⏱️ Updates every 30 seconds")


if selected == "Live Algo Trading":
    st.title("🤖 Live Algo Trading (Paper/Real Mode)")
    from dotenv import load_dotenv

    load_dotenv()
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    def send_telegram(msg: str):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            st.error(f"Telegram Error: {e}")

    start_msg = "🟢 Strategy Test Started"
    st.info(start_msg)
    send_telegram(start_msg)

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

    now = latest.name
    if now.hour == 9 and now.minute == 15:
        market_msg = "📈 Market Opened at 09:15 But My Doctor Strategy will Start 09:30 "
        st.success(market_msg)
        send_telegram(market_msg)

    if now.hour == 14 and now.minute == 30:
        market_close_msg = "📉 Doctor Strategy will not take Trade after 02:30"
        st.warning(market_close_msg)
        send_telegram(market_close_msg)

    if now.hour == 15 and now.minute == 30:
        market_close_msg = "📉 Market Closed at 15:30 Bye! See you Tomorrow 9:30"
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

    # ─── TREND LOGIC ───────────────────────────────────────────────────────────────
    def get_trend(data):
        data["EMA20"] = ta.trend.ema_indicator(data["Close"], window=20).ema_indicator()
        data["EMA50"] = ta.trend.ema_indicator(data["Close"], window=50).ema_indicator()
        latest = data.iloc[-1]
        if latest["EMA20"] > latest["EMA50"]:
            return "UP"
        elif latest["EMA20"] < latest["EMA50"]:
            return "DOWN"
        else:
            return "SIDEWAYS"

    def fetch_nifty_trends():
        symbol = "^NSEI"
        trends = {}
        intervals = {
            "5min": ("5m", "7d"),
            "15min": ("15m", "30d"),
            "daily": ("1d", "3mo"),
            "weekly": ("1wk", "1y"),
            "monthly": ("1mo", "5y")
        }

        for label, (interval, period) in intervals.items():
            data = yf.download(symbol, interval=interval, period=period, progress=False)
            if not data.empty:
                trend = get_trend(data)
                trends[label] = trend
            else:
                trends[label] = "No Data"

        return trends

    trends = fetch_nifty_trends()
    for tf, trend in trends.items():
        st.markdown(f"**{tf.upper()} Trend ➜** `{trend}`")

    # ─── DISPLAY ──────────────────────────────────────────────────────────────────
    st.subheader("📊 Last 5 Candles")
    st.dataframe(df.tail(5))

    col1, col2, col3 = st.columns(3)
    col1.metric("🔹 Close", f"₹{latest['Close']:.2f}")
    col2.metric("🔸 EMA20", f"₹{latest['EMA20']:.2f}")
    col3.metric("📌 Signal", signal)
