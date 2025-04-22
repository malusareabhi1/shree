import streamlit as st
import pandas as pd
import requests
#import datetime
from kiteconnect import KiteConnect
import pytz
#from datetime 
import datetime
import time

# Telegram and Trading Configurations
TELEGRAM_TOKEN = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
CHAT_ID = "1320205499"

# Define market time windows
START_TIME = datetime.time(9, 30)
END_TIME = datetime.time(14, 30)
PRE_MARKET_START = datetime.time(9, 0)
PRE_MARKET_END = datetime.time(9, 15)
MARKET_CLOSE = datetime.time(15, 30)

# Function to send Telegram message
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")


ist = pytz.timezone("Asia/Kolkata")

now = datetime.datetime.now(ist)
now = datetime.now().strftime("%H:%M:%S")
# Check current time
#now = datetime.datetime.now().time()
today = datetime.datetime.today().weekday()  # Monday = 0, Sunday = 6
st.write(now)
# Only operate on weekdays (Mon-Fri)
if today < 5:
    if PRE_MARKET_START <= now < PRE_MARKET_END:
        send_telegram_message("📢 Pre market Open")
        st.info("Pre market Open")
    elif datetime.time(9, 15) <= now < MARKET_CLOSE:
        send_telegram_message("✅ Market is open now to ALGOTRADE")
        st.success("Market is open now to ALGOTRADE")
    elif now >= MARKET_CLOSE:
        send_telegram_message("📉 Market is closed now")
        st.warning("Market is closed now")

# Check trading window for strategy
if now < START_TIME or now > END_TIME:
    send_telegram_message("⛔ Outside trading time. Doctor Strategy will not take trades now.")
    st.warning("Outside trading time. No trades will be taken.")
    st.stop()

# --- Start of Main Algo Streamlit Code ---
st.title("🩺 Doctor Strategy 1.0 - Live Algo Trading")

# Placeholder for KiteConnect initialization and strategy logic
st.write("Welcome to Doctor Strategy 1.0 Algo Bot")

# Add Start and Stop buttons
start_button = st.sidebar.button("Start Algo Trading")
stop_button = st.sidebar.button("Stop Algo Trading")

if start_button:
    st.session_state.is_trading_active = True
    st.write("🟢 Trading started...")

if stop_button:
    st.session_state.is_trading_active = False
    st.write("🔴 Trading stopped.")

# Use the flag `is_trading_active` to control your trading logic
if 'is_trading_active' not in st.session_state:
    st.session_state.is_trading_active = False  # Default to not trading

# Main trading logic loop (Placeholder)
if st.session_state.is_trading_active:
    # Replace with your actual trading logic, e.g. order placements, fetching data, etc.
    st.write("Executing trades...")  # Example placeholder
else:
    st.write("Trading is stopped. No trades are being executed.")
