import streamlit as st
import pandas as pd
import os
import requests
from datetime import datetime, time as dt_time
import pytz
from dotenv import load_dotenv
import os

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # optionally, use .env for chat_id too

bot_token= os.getenv("TELEGRAM_BOT_TOKEN")
chat_id= os.getenv("TELEGRAM_CHAT_ID")  # optionally, use .env for chat_id too
def send_telegram_message(msg):
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=payload)
    except:
        st.warning("⚠️ Failed to send Telegram message.")

# ========== Market Time Check ==========
def is_market_open():
    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india).time()
    return dt_time(9, 15) <= now <= dt_time(15, 30)

# ========== Apply Strategy ==========
def apply_doctor_strategy(df, symbol, capital, sl_percent):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VMA20'] = df['Volume'].rolling(20).mean()

    in_position = False
    entry = 0
    sl = 0
    qty = 0
    log = []

    for i in range(21, len(df)):
        price = df['Close'].iloc[i]
        prev_close = df['Close'].iloc[i - 1]
        ema = df['EMA20'].iloc[i]
        prev_ema = df['EMA20'].iloc[i - 1]
        volume = df['Volume'].iloc[i]
        vma = df['VMA20'].iloc[i]

        timestamp = df.index[i]

        if not in_position:
            if prev_close < prev_ema and price > ema and volume > vma:
                entry = price
                sl = round(entry * (1 - sl_percent / 100), 2)
                qty = int(capital / entry)
                in_position = True

                msg = f"📥 <b>TEST BUY</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ₹{entry}\n<b>SL:</b> ₹{sl}\n<b>Qty:</b> {qty}\n<b>Time:</b> {timestamp}"
                send_telegram_message(msg)
                log.append([timestamp, symbol, "BUY", entry, qty, sl])
        
        else:
            if price <= sl:
                msg = f"📤 <b>TEST SELL</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ₹{price}\n<b>Reason:</b> SL Hit\n<b>Time:</b> {timestamp}"
                send_telegram_message(msg)
                log.append([timestamp, symbol, "SELL", price, qty, sl])
                in_position = False
                entry = 0
                sl = 0
                qty = 0

            else:
                new_sl = round(price * (1 - sl_percent / 100), 2)
                if new_sl > sl:
                    sl = new_sl
                    send_telegram_message(f"🔁 <b>Trailing SL Updated</b> for {symbol} to ₹{sl}")

    return log

# ========== UI ==========
st.title("🔍 Backtest Strategy on CSV (Market Closed Mode)")

if not is_market_open():
    st.warning("📴 Market is closed. Running backtest mode.")

    uploaded_files = st.file_uploader("📂 Upload CSV files (1 per stock)", type="csv", accept_multiple_files=True)
    capital = st.number_input("💰 Capital Allocation", value=50000)
    sl_percent = st.slider("🔻 SL %", 0.5, 5.0, value=1.5)

    if uploaded_files:
        all_logs = []
        for file in uploaded_files:
            symbol = file.name.replace(".csv", "")
            df = pd.read_csv(file, parse_dates=['Datetime'], index_col='Datetime')
            df.dropna(inplace=True)
            st.write(f"📊 Processing {symbol}")
            logs = apply_doctor_strategy(df, symbol, capital, sl_percent)
            all_logs.extend(logs)

        if all_logs:
            result_df = pd.DataFrame(all_logs, columns=["Timestamp", "Symbol", "Action", "Price", "Qty", "SL"])
            st.dataframe(result_df)
            result_df.to_csv("backtest_log.csv", index=False)
            st.success("✅ Backtest Complete. Alerts sent. Log saved as backtest_log.csv")

else:
    st.success("✅ Market is open. Please use Live Algo Trading mode.")
  
    st.header("🟢 Live Algo Trading Mode")
    uploaded_files = st.file_uploader("📂 Upload Live CSV (Auto-refresh every minute suggested)", type="csv", accept_multiple_files=True)
    capital = st.number_input("💰 Capital Allocation", value=50000)
    sl_percent = st.slider("🔻 SL %", 0.5, 5.0, value=1.5)
    
    if uploaded_files:
        st.info("📡 Monitoring Live Signals...")

        status_dict = {}  # to avoid duplicate alerts in session

        for file in uploaded_files:
            symbol = file.name.replace(".csv", "")
            df = pd.read_csv(file, parse_dates=['Datetime'], index_col='Datetime')
            df.dropna(inplace=True)

            if symbol not in status_dict:
                status_dict[symbol] = {"in_position": False, "entry": 0, "sl": 0, "qty": 0}

            # latest candle only
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
            vma20 = df['Volume'].rolling(20).mean().iloc[-1]

            price = latest['Close']
            volume = latest['Volume']
            timestamp = df.index[-1]

            status = status_dict[symbol]

            if not status["in_position"]:
                if prev['Close'] < ema20 and price > ema20 and volume > vma20:
                    entry = price
                    sl = round(entry * (1 - sl_percent / 100), 2)
                    qty = int(capital / entry)

                    status.update({"in_position": True, "entry": entry, "sl": sl, "qty": qty})

                    msg = f"📥 <b>LIVE BUY</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ₹{entry}\n<b>SL:</b> ₹{sl}\n<b>Qty:</b> {qty}\n<b>Time:</b> {timestamp}"
                    send_telegram_message(msg)
                    st.success(f"📈 LIVE BUY Signal for {symbol} at ₹{entry}")

            else:
                if price <= status["sl"]:
                    msg = f"📤 <b>LIVE SELL</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ₹{price}\n<b>Reason:</b> SL Hit\n<b>Time:</b> {timestamp}"
                    send_telegram_message(msg)
                    st.error(f"📉 LIVE SELL for {symbol} at ₹{price}")
                    status_dict[symbol] = {"in_position": False, "entry": 0, "sl": 0, "qty": 0}

                else:
                    new_sl = round(price * (1 - sl_percent / 100), 2)
                    if new_sl > status["sl"]:
                        status["sl"] = new_sl
                        send_telegram_message(f"🔁 <b>Trailing SL Updated</b> for {symbol} to ₹{new_sl}")
                        st.info(f"🔁 SL Trailed for {symbol}: ₹{new_sl}")

