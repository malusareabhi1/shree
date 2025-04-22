import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

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

# ========== Streamlit UI ==========
st.set_page_config(page_title="Doctor Strategy 1.0", layout="centered")
st.title("🧠 Doctor Strategy 1.0 (Paper Trading + Telegram Alerts)")

symbol = st.text_input("📈 Stock Symbol (e.g., INFY.NS)", value="INFY.NS")
capital = st.number_input("💰 Capital Allocation", value=50000)
sl_percent = st.slider("🔻 Initial SL (%)", 0.5, 5.0, value=1.0)
interval = st.selectbox("🕒 Interval", ["1m", "5m", "15m"], index=1)
run = st.button("🚀 Start Strategy")

# ========== Strategy Logic ==========
def fetch_data(symbol, interval):
    df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
    df.dropna(inplace=True)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VMA20'] = df['Volume'].rolling(window=20).mean()
    return df

if run and symbol:
    st.success("📡 Running Doctor Strategy... Signals will be sent to Telegram.")
    placeholder = st.empty()
    in_position = False
    entry_price = 0
    trailing_sl = 0
    qty = 0

    while True:
        try:
            df = fetch_data(symbol, interval)
            if len(df) < 21:
                st.warning("📉 Not enough data yet. Waiting for more candles...")
                time.sleep(60)
                continue

            # Extract latest values
            price = df['Close'].iloc[-1].item()
            prev_close = df['Close'].iloc[-2].item()

            ema = df['EMA20'].iloc[-1].item()
            prev_ema = df['EMA20'].iloc[-2].item()

            volume = df['Volume'].iloc[-1].item()
            vma = df['VMA20'].iloc[-1].item()

            # === Entry ===
            if not in_position:
                crossed_above = prev_close < prev_ema and price > ema
                high_volume = volume > vma

                if crossed_above and high_volume:
                    entry_price = price
                    qty = int(capital / entry_price)
                    trailing_sl = round(entry_price * (1 - sl_percent / 100), 2)
                    in_position = True

                    st.success(f"📥 BUY @ ₹{entry_price}")
                    send_telegram_message(f"📥 <b>BUY SIGNAL</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ₹{entry_price}\n<b>SL:</b> ₹{trailing_sl}\n<b>Qty:</b> {qty}")

            # === Exit / Update ===
            elif in_position:
                # Update trailing SL
                new_trailing_sl = round(price * (1 - sl_percent / 100), 2)
                if new_trailing_sl > trailing_sl:
                    trailing_sl = new_trailing_sl
                    send_telegram_message(f"🔁 <b>Trailing SL Updated</b>\n<b>New SL:</b> ₹{trailing_sl}")

                # Exit on SL hit
                if price <= trailing_sl:
                    st.error(f"📤 SELL @ ₹{price} (SL Hit)")
                    send_telegram_message(f"📤 <b>SELL SIGNAL</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ₹{price}\n<b>Reason:</b> SL Hit")
                    in_position = False
                    entry_price = 0
                    trailing_sl = 0

            # === UI ===
            with placeholder.container():
                st.metric("💹 Live Price", f"₹{price}")
                st.metric("📈 EMA20", f"₹{ema}")
                st.metric("🔊 Volume", f"{int(volume)}")
                st.metric("📉 Trailing SL", f"₹{trailing_sl if in_position else '---'}")
                st.metric("🧮 Position", "IN TRADE" if in_position else "WAITING")

            time.sleep(60)

        except Exception as e:
            st.error(f"❌ Error: {e}")
            send_telegram_message(f"❌ <b>Error</b>\n{e}")
            break
