import streamlit as st
import pandas as pd
#from datetime import datetime
import datetime
import time
from kiteconnect import KiteConnect, KiteTicker
import requests
import os
#import pytz
# ======================
# CONFIGURATION
# ======================
API_KEY = "your_zerodha_api_key"
API_SECRET = "your_zerodha_api_secret"
ACCESS_TOKEN = "your_access_token"  # Load from file or login flow
BOT_TOKEN = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
CHAT_ID = "1320205499"
capital_per_trade = 10000
stop_loss_percent = 5
symbol = "^NSE"
trading_start = datetime.time(9, 30)
trading_end = datetime.time(14, 30)
TRAILING_SL_STEP = 10  # Rs profit trail step

# ======================
# INITIALIZE
# ======================
kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

if "trade_log" not in st.session_state:
    st.session_state.trade_log = []
    st.session_state.trade_status = "Idle"
    st.session_state.trailing_sl = None
    st.session_state.entry_price = None
    st.session_state.in_position = False

# ======================
# FUNCTIONS
# ======================

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def fetch_option_iv(symbol="NIFTY", strike_type="CE"):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(url, headers=headers).json()
        records = response["records"]["data"]
        for r in records:
            ce = r.get("CE")
            if ce and ce["strikePrice"] >= r["strikePrice"]:
                return ce["impliedVolatility"]
    except:
        return 0.0
    return 0.0

def get_ltp(symbol):
    quote = kite.ltp(f"NSE:{symbol}")
    return quote[f"NSE:{symbol}"]["last_price"]

def place_market_order(symbol, qty, transaction_type="BUY"):
    return kite.place_order(
        variety=kite.VARIETY_REGULAR,
        exchange=kite.EXCHANGE_NSE,
        tradingsymbol=symbol,
        transaction_type=transaction_type,
        quantity=qty,
        order_type=kite.ORDER_TYPE_MARKET,
        product=kite.PRODUCT_MIS
    )

def trail_stop_loss(current_price):
    if st.session_state.entry_price and st.session_state.in_position:
        profit = current_price - st.session_state.entry_price
        if profit > TRAILING_SL_STEP:
            st.session_state.trailing_sl = st.session_state.entry_price + (profit - TRAILING_SL_STEP)

def monitor_trade(symbol, qty):
    while True:
        now = datetime.datetime.now().time()
        if now >= trading_end:
            place_market_order(symbol, qty, "SELL")
            send_telegram_message(f"Auto Exit at 2:30 PM - {symbol}")
            st.session_state.in_position = False
            break

        ltp = get_ltp(symbol)
        trail_stop_loss(ltp)

        if ltp <= st.session_state.trailing_sl:
            place_market_order(symbol, qty, "SELL")
            send_telegram_message(f"Trailing SL HIT - Exited {symbol} at {ltp}")
            st.session_state.in_position = False
            break

        time.sleep(10)

def log_trade(entry_price, sl, qty, mode):
    log = {
        "Time": datetime.datetime.now().strftime("%H:%M:%S"),
        "Symbol": symbol,
        "Entry": entry_price,
        "SL": sl,
        "Qty": qty,
        "Mode": mode
    }
    st.session_state.trade_log.append(log)
    df = pd.DataFrame(st.session_state.trade_log)
    df.to_csv("doctor_strategy_trade_log.csv", index=False)

# ======================
# STREAMLIT UI
# ======================

st.title("🩺 Doctor Strategy 1.0 Live ")
mode = st.sidebar.selectbox("Mode", ["Paper", "Live"])
run = st.sidebar.button("▶️ Start")

import datetime
import pytz

ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.datetime.now(ist)
#print("📈 Indian Share Market Time (IST):", now_ist.strftime("%Y-%m-%d %H:%M:%S"))
st.write(f"Current time in India (IST): {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")

if run:
        # Define IST timezone
    ist = pytz.timezone("Asia/Kolkata")
    
    # Get current IST datetime
    now_ist = datetime.now(ist).time()  # Get current time in IST
    #now_ist = datetime.now(ist)
    #now_ist = datetime.datetime.now(ist)
    # Option A: Format with strftime for time only
    #time_str = now_ist.strftime("%H:%M:%S")
    st.write(f"⏰ Current IST Time: {now_ist}")
    #now = datetime.datetime.now().time()
    #now = datetime.datetime.now(ist)
    # Get current IST time
    #now = datetime.now(ist).time()  # Use .time() to get only the time portion
    if trading_start <= now <= trading_end:
        iv = fetch_option_iv()
        if iv > 16:
            ltp = get_ltp(symbol)
            qty = int(capital_per_trade / ltp)
            sl_price = round(ltp - (ltp * stop_loss_percent / 100), 2)

            st.session_state.entry_price = ltp
            st.session_state.trailing_sl = ltp - (ltp * stop_loss_percent / 100)
            st.session_state.in_position = True

            if mode == "Live":
                place_market_order(symbol, qty, "BUY")
                send_telegram_message(f"Live Trade Executed: {symbol} @ {ltp} SL: {sl_price}")
            else:
                send_telegram_message(f"Paper Trade: {symbol} @ {ltp} SL: {sl_price}")

            log_trade(ltp, sl_price, qty, mode)
            monitor_trade(symbol, qty)
        else:
            st.warning("IV < 16. No Trade.")
    else:
        st.info("Outside trading time.")

# ======================
# LOGS
# ======================

st.subheader("📜 Trade Log")
if st.session_state.trade_log:
    df = pd.DataFrame(st.session_state.trade_log)
    st.dataframe(df)
    st.download_button("⬇️ Download CSV", data=df.to_csv(index=False), file_name="doctor_strategy_trade_log.csv")
else:
    st.info("No trades yet.")
