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
def run_strategy_on_df(df, symbol, capital=50000, sl_pct=1.0):
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

    trade_log = []

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

            msg = f"📥 BUY {symbol}: ₹{entry} | SL: ₹{sl} | Qty: {qty} @ {ts}"
            send_telegram(msg)
            entry_logs.append(msg)
            trade_log.append([ts, symbol, "BUY", entry, qty, sl])

        # Exit
        elif in_position and price <= sl:
            exit_msg = f"📤 SELL {symbol}: ₹{price} (SL Hit) @ {ts}"
            send_telegram(exit_msg)
            exit_logs.append(exit_msg)
            trade_log.append([ts, symbol, "SELL", price, qty, sl])

            profit = (price - entry) * qty
            pnl += profit
            in_position = False

    return entry_logs, exit_logs, pnl, trade_log

# ===== Streamlit App =====
st.set_page_config("📉 Strategy Tester", layout="centered")
st.title("📊 Doctor Strategy Backtest (Multiple CSVs + Alerts + PnL)")

if not is_market_open():
    st.warning("📴 Market is closed — testing strategy on uploaded CSV data.")

    uploaded_files = st.file_uploader("📂 Upload CSV files (1 per stock)", type="csv", accept_multiple_files=True)
    capital = st.number_input("💰 Capital per Symbol", value=50000)
    sl_percent = st.slider("🔻 SL %", 0.5, 5.0, value=1.5)

    if uploaded_files:
        all_trade_logs = []
        total_pnl = 0
        pnl_summary = []

        for file in uploaded_files:
            symbol = file.name.replace(".csv", "")
            df = pd.read_csv(file, parse_dates=["Datetime"])
            df.set_index("Datetime", inplace=True)

            st.write(f"📈 Processing: `{symbol}`")

            entries, exits, pnl, log = run_strategy_on_df(df, symbol, capital, sl_percent)
            all_trade_logs.extend(log)
            pnl_summary.append({"Symbol": symbol, "PnL": pnl})
            total_pnl += pnl

            with st.expander(f"📥 {symbol} Entry/Exit Logs"):
                st.write(entries + exits or "No trades.")

        # ===== Save trade log to CSV =====
        result_df = pd.DataFrame(all_trade_logs, columns=["Timestamp", "Symbol", "Action", "Price", "Qty", "SL"])
        result_df.to_csv("backtest_log.csv", index=False)
        st.success("✅ Strategy complete. Log saved as `backtest_log.csv`")

        # ===== Show PnL Summary =====
        pnl_df = pd.DataFrame(pnl_summary)
        st.subheader("💰 PnL Summary per Symbol")
        st.dataframe(pnl_df)
        st.metric("📊 Total PnL", f"₹{total_pnl:.2f}")

else:
    st.info("✅ Market is open. Use Live Trading mode.")
