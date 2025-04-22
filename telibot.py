import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time as dt_time
import pytz
import io

# ===== Telegram Setup =====
bot_token = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
chat_id = "1320205499"

def send_telegram(msg):
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
        )
        if res.status_code != 200:
            st.warning("⚠️ Telegram message failed to send.")
    except Exception as e:
        st.warning(f"⚠️ Telegram error: {e}")

# ===== Market Open Check (India NSE) =====
def is_market_open():
    now = datetime.now(pytz.timezone("Asia/Kolkata")).time()
    return dt_time(9, 15) <= now <= dt_time(15, 30)

# ===== Strategy Simulation on CSV =====
def run_strategy_on_csv(df, capital=50000, sl_pct=1.0):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["VMA20"] = df["Volume"].rolling(window=20).mean()
    df.dropna(inplace=True)

    entry_logs = []
    exit_logs = []
    in_position = False
    entry = 0
    sl = 0
    qty = 0
    pnl = 0

    for i in range(1, len(df)):
        ts = df.index[i]
        price = df["Close"].iloc[i]
        volume = df["Volume"].iloc[i]
        ema = df["EMA20"].iloc[i]
        vma = df["VMA20"].iloc[i]

        prev_close = df["Close"].iloc[i - 1]
        prev_ema = df["EMA20"].iloc[i - 1]

        # Entry
        if not in_position and prev_close < prev_ema and price > ema and volume > vma:
            entry = price
            qty = int(capital / price)
            sl = round(entry * (1 - sl_pct / 100), 2)
            in_position = True

            entry_msg = f"📥 BUY: ₹{price} | SL: ₹{sl} | Qty: {qty} @ {ts}"
            entry_logs.append(entry_msg)
            send_telegram(entry_msg)

        # Exit
        elif in_position and price <= sl:
            exit_msg = f"📤 SELL: ₹{price} (SL Hit) @ {ts}"
            exit_logs.append(exit_msg)
            send_telegram(exit_msg)

            profit = (price - entry) * qty
            pnl += profit
            in_position = False

    return entry_logs, exit_logs, pnl

# ===== Streamlit App =====
st.set_page_config("📉 Strategy Tester", layout="centered")
st.title("📊 Doctor Strategy Backtest (CSV + Telegram Alerts)")

if not is_market_open():
    st.warning("📴 Market is closed — running strategy on uploaded data.")

    uploaded_file = st.file_uploader("📂 Upload CSV (Datetime, Open, High, Low, Close, Volume)", type="csv")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, parse_dates=["Datetime"])
            df.set_index("Datetime", inplace=True)

            st.success("✅ Data loaded. Running strategy...")

            entry_logs, exit_logs, pnl = run_strategy_on_csv(df)

            st.subheader("📥 Entries")
            st.write(entry_logs or "No entries")

            st.subheader("📤 Exits")
            st.write(exit_logs or "No exits")

            st.metric("💰 Net PnL", f"₹{pnl:.2f}")

        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
else:
    st.info("✅ Market is open. Use Live mode.")
