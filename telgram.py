import streamlit as st
import pandas as pd
import requests
from kiteconnect import KiteConnect
import pytz
import datetime
import time

# Telegram Config
TELEGRAM_TOKEN = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
CHAT_ID = "1320205499"

# Define Time Windows
START_TIME = datetime.time(9, 30)
END_TIME = datetime.time(14, 30)
PRE_MARKET_START = datetime.time(9, 0)
PRE_MARKET_END = datetime.time(9, 15)
MARKET_CLOSE = datetime.time(15, 30)

# Telegram Message Sender
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# Initialize Session State
if "sent_pre_market" not in st.session_state:
    st.session_state.sent_pre_market = False
if "sent_market_open" not in st.session_state:
    st.session_state.sent_market_open = False
if "sent_market_closed" not in st.session_state:
    st.session_state.sent_market_closed = False
if "sent_out_of_time" not in st.session_state:
    st.session_state.sent_out_of_time = False
if "is_trading_active" not in st.session_state:
    st.session_state.is_trading_active = False

# Get current IST time
ist = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(ist).time()
today = datetime.datetime.now(ist).weekday()  # 0 = Monday

st.write(f"Current Time (IST): {now}")

# Only operate Mon–Fri
if today < 5:
    if PRE_MARKET_START <= now < PRE_MARKET_END:
        if not st.session_state.sent_pre_market:
            send_telegram_message("📢 Pre market Open")
            st.session_state.sent_pre_market = True
        st.info("Pre market Open")

    elif datetime.time(9, 15) <= now < MARKET_CLOSE:
        if not st.session_state.sent_market_open:
            send_telegram_message("✅ Market is open now to ALGOTRADE")
            st.session_state.sent_market_open = True
        st.success("Market is open now to ALGOTRADE")

    elif now >= MARKET_CLOSE:
        if not st.session_state.sent_market_closed:
            send_telegram_message("📉 Market is closed now")
            st.session_state.sent_market_closed = True
        st.warning("Market is closed now")
        st.stop()  # Shut down the program after market close

# Check if current time is outside strategy time window
if now < START_TIME or now > END_TIME:
    if not st.session_state.sent_out_of_time:
        send_telegram_message("⛔ Outside trading time. Doctor Strategy will not take trades now.")
        st.session_state.sent_out_of_time = True
    st.warning("Outside trading time. No trades will be taken.")
    st.stop()

# Main UI
st.title("🩺 Doctor Strategy 1.0 - Live Algo Trading")

start_button = st.sidebar.button("Start Algo Trading")
stop_button = st.sidebar.button("Stop Algo Trading")

if start_button:
    st.session_state.is_trading_active = True
    st.success("🟢 Trading started...")

if stop_button:
    st.session_state.is_trading_active = False
    st.warning("🔴 Trading stopped.")

if st.session_state.is_trading_active:
    st.write("Executing trades...")  # 🔄 Replace with actual logic
else:
    st.write("Trading is stopped. No trades are being executed.")
