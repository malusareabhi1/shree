import streamlit as st
import pandas as pd
import datetime
import time
from kiteconnect import KiteConnect
import requests
import os
import pytz

# ======================
# CONFIGURATION
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # optionally, use .env for chat_id too

# ======================

capital_per_trade = 10000
stop_loss_percent = 5
symbol = "^NSE"
trading_start = datetime.time(9, 30)
trading_end = datetime.time(14, 30)
TRAILING_SL_STEP = 10

# ======================
# KITE LOGIN HANDLING
# ======================
st.sidebar.title("\ud83d\udd10 Kite Login")

kite = KiteConnect(api_key=API_KEY)
ACCESS_TOKEN_FILE = "access_token.txt"

# Function to load saved token
def load_saved_token():
    if os.path.exists(ACCESS_TOKEN_FILE):
        with open(ACCESS_TOKEN_FILE, "r") as f:
            return f.read().strip()
    return None

# Function to save new token
def save_access_token(token):
    with open(ACCESS_TOKEN_FILE, "w") as f:
        f.write(token)

# Login process
access_token = load_saved_token()
logged_in = False

if access_token:
    try:
        kite.set_access_token(access_token)
        profile = kite.profile()
        st.success("\u2705 Successfully connected to Kite!")
        st.markdown(f"**User ID:** `{profile['user_id']}`")
        st.markdown(f"**User Name:** `{profile['user_name']}`")
        st.markdown(f"**Email:** `{profile['email']}`")
        st.markdown(f"**Broker:** `{profile['broker']}`")
        logged_in = True
    except Exception:
        st.warning("\u26a0\ufe0f Saved token expired or invalid. Please login again.")
        os.remove(ACCESS_TOKEN_FILE)

if not logged_in:
    login_url = kite.login_url()
    st.sidebar.markdown(f"[\ud83d\udded Click here to login with Kite]({login_url})")
    request_token = st.sidebar.text_input("Paste request_token from redirect URL:")

    if st.sidebar.button("\ud83d\udd13 Generate Session"):
        try:
            data = kite.generate_session(request_token, api_secret=API_SECRET)
            access_token = data["access_token"]
            kite.set_access_token(access_token)
            save_access_token(access_token)
            profile = kite.profile()
            st.success("\u2705 Successfully connected to Kite!")
            st.markdown(f"**User ID:** `{profile['user_id']}`")
            st.markdown(f"**User Name:** `{profile['user_name']}`")
            st.markdown(f"**Email:** `{profile['email']}`")
            st.markdown(f"**Broker:** `{profile['broker']}`")
        except Exception as e:
            st.error(f"\u274c Login failed: {str(e)}")

# ======================
# STATE INIT
# ======================
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
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def fetch_option_iv(symbol="NIFTY", strike_type="CE"):
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {"User-Agent": "Mozilla/5.0"}
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
st.title("\ud83e\uddf5 Doctor Strategy 1.0 Live Trading")
ist = pytz.timezone("Asia/Kolkata")
now = datetime.datetime.now(ist).time()
st.write("Time") 
st.write(now)

today = datetime.datetime.today().weekday()

mode = st.sidebar.selectbox("Mode", ["Paper", "Live"])
run = st.sidebar.button("\u25b6\ufe0f Start")
stop = st.sidebar.button("\u23f9\ufe0f Stop")

if stop:
    st.stop()
    st.success("Thank you for Trade .")

if run:
    now = datetime.datetime.now(ist).time()
    if trading_start <= now <= trading_end:
        iv = fetch_option_iv()
        st.write("IV")
        st.write(iv)
        if iv >= 0:
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
st.subheader("\ud83d\udcdc Trade Log")
if st.session_state.trade_log:
    df = pd.DataFrame(st.session_state.trade_log)
    st.dataframe(df)
    st.download_button("\u2b07\ufe0f Download CSV", data=df.to_csv(index=False), file_name="doctor_strategy_trade_log.csv")
else:
    st.info("No trades yet.")
