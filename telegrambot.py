import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
import datetime
import os

# ========== Telegram Setup ==========
bot_token = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
chat_id = "1320205499"

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

# ========== CSV Logger ==========
def log_trade(symbol, action, price, qty, sl):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data = pd.DataFrame([[now, symbol, action, price, qty, sl]], columns=["Timestamp", "Symbol", "Action", "Price", "Qty", "SL"])
    if not os.path.exists("trade_log.csv"):
        data.to_csv("trade_log.csv", index=False)
    else:
        data.to_csv("trade_log.csv", mode='a', header=False, index=False)

# ========== Streamlit UI ==========
st.set_page_config(page_title="Doctor Strategy 1.1", layout="centered")
st.title("🧠 Doctor Strategy 1.1 (Multi-Stock + Paper Trade + Telegram)")

symbols_input = st.text_input("📈 Stock Symbols (comma-separated, e.g., INFY.NS, RELIANCE.NS)", value="INFY.NS, RELIANCE.NS")
capital = st.number_input("💰 Capital Allocation (per stock)", value=50000)
sl_percent = st.slider("🔻 Initial SL (%)", 0.5, 5.0, value=1.0)
interval = st.selectbox("🕒 Interval", ["1m", "5m", "15m"], index=1)
start_btn = st.button("🚀 Start Strategy")
stop_btn = st.button("🛑 Stop Strategy")
placeholder = st.empty()

# Session flag
if 'running' not in st.session_state:
    st.session_state.running = False

# ========== Fetch Strategy Data ==========
def fetch_data(symbol, interval):
    df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
    df.dropna(inplace=True)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VMA20'] = df['Volume'].rolling(window=20).mean()
    return df

# ========== Main Strategy ==========
if start_btn:
    st.session_state.running = True

if stop_btn:
    st.session_state.running = False
    st.warning("🛑 Strategy Stopped.")

if st.session_state.running:
    symbols = [s.strip().upper() for s in symbols_input.split(",")]
    positions = {sym: {"in_position": False, "entry": 0, "sl": 0, "qty": 0} for sym in symbols}

    while st.session_state.running:
        for symbol in symbols:
            try:
                df = fetch_data(symbol, interval)
                if len(df) < 21:
                    continue

                # Extract values
                price = df['Close'].iloc[-1].item()
                prev_close = df['Close'].iloc[-2].item()
                ema = df['EMA20'].iloc[-1].item()
                prev_ema = df['EMA20'].iloc[-2].item()
                volume = df['Volume'].iloc[-1].item()
                vma = df['VMA20'].iloc[-1].item()

                pos = positions[symbol]

                # === Entry ===
                if not pos['in_position']:
                    if prev_close < prev_ema and price > ema and volume > vma:
                        entry_price = price
                        qty = int(capital / entry_price)
                        sl = round(entry_price * (1 - sl_percent / 100), 2)
                        pos.update({"in_position": True, "entry": entry_price, "sl": sl, "qty": qty})

                        msg = f"📥 <b>BUY SIGNAL</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ₹{entry_price}\n<b>SL:</b> ₹{sl}\n<b>Qty:</b> {qty}"
                        send_telegram_message(msg)
                        log_trade(symbol, "BUY", entry_price, qty, sl)

                # === Exit ===
                elif pos['in_position']:
                    if price <= pos["sl"]:
                        msg = f"📤 <b>SELL SIGNAL</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ₹{price}\n<b>Reason:</b> SL Hit"
                        send_telegram_message(msg)
                        log_trade(symbol, "SELL", price, pos["qty"], pos["sl"])
                        pos.update({"in_position": False, "entry": 0, "sl": 0, "qty": 0})

                    else:
                        # Trailing SL logic
                        new_sl = round(price * (1 - sl_percent / 100), 2)
                        if new_sl > pos["sl"]:
                            pos["sl"] = new_sl
                            send_telegram_message(f"🔁 <b>Trailing SL Updated</b>\n<b>{symbol} SL:</b> ₹{new_sl}")

            except Exception as e:
                st.error(f"{symbol} ❌ {e}")
                send_telegram_message(f"❌ <b>{symbol} Error</b>\n{e}")

        # === Display Live Status ===
        with placeholder.container():
            st.subheader("📊 Live Positions")
            for symbol in symbols:
                pos = positions[symbol]
                st.write(f"**{symbol}** → {'🟢 IN POSITION' if pos['in_position'] else '⚪ WAITING'} | Entry: ₹{pos['entry']} | SL: ₹{pos['sl']} | Qty: {pos['qty']}")

        time.sleep(60)  # Wait before next scan
