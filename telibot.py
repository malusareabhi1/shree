import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time as dt_time
import pytz

# ===== Telegram Setup =====
bot_token = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
chat_id = "1320205499"
def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
        )
    except:
        pass

# ===== Market Time Check (IST) =====
def is_market_open():
    now = datetime.now(pytz.timezone("Asia/Kolkata")).time()
    return dt_time(9, 15) <= now <= dt_time(15, 30)

# ===== Test Mode: Strategy on CSV =====
def run_strategy_on_csv(file, capital=50000, sl_pct=1.0):
    df = pd.read_csv(file, parse_dates=["Datetime"])
    df.set_index("Datetime", inplace=True)
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["VMA20"] = df["Volume"].rolling(window=20).mean()
    df.dropna(inplace=True)

    in_position = False
    entry = 0
    sl = 0
    qty = 0

    for ts, row in df.iterrows():
        price = row["Close"]
        volume = row["Volume"]
        ema = row["EMA20"]
        vma = row["VMA20"]
        prev_close = df.loc[:ts].iloc[-2]["Close"] if len(df.loc[:ts]) > 1 else price
        prev_ema = df.loc[:ts].iloc[-2]["EMA20"] if len(df.loc[:ts]) > 1 else ema

        # Entry Condition
        if not in_position and prev_close < prev_ema and price > ema and volume > vma:
            entry = price
            qty = int(capital / price)
            sl = round(price * (1 - sl_pct / 100), 2)
            in_position = True

            msg = f"📥 <b>PAPER BUY</b>\n<b>Time:</b> {ts}\n<b>Price:</b> ₹{price}\n<b>SL:</b> ₹{sl}\n<b>Qty:</b> {qty}"
            send_telegram(msg)
            st.success(msg)

        # Exit Condition
        elif in_position and price <= sl:
            in_position = False
            msg = f"📤 <b>PAPER SELL</b>\n<b>Time:</b> {ts}\n<b>Exit:</b> ₹{price} (SL Hit)"
            send_telegram(msg)
            st.error(msg)

# ===== Streamlit App =====
st.title("📊 Doctor Strategy Backtest (CSV + Telegram)")

if not is_market_open():
    st.warning("🔁 Market is closed. Running strategy in test mode.")

    uploaded_file = st.file_uploader("📂 Upload CSV with OHLCV data", type="csv")
    if uploaded_file:
        st.success("✅ File uploaded. Running test strategy...")
        run_strategy_on_csv(uploaded_file)

else:
    st.info("✅ Market is open. Use Live Mode for real-time trading.")
