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
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=payload)

# ========== Streamlit UI ==========
st.title("🧠 Doctor Strategy 1.0 - Paper Algo Trading")

symbol = st.text_input("📈 Symbol (e.g., INFY.NS)", value="INFY.NS")
capital = st.number_input("💰 Capital Allocation", value=50000)
sl_percent = st.slider("🔻 Initial SL (%)", min_value=0.5, max_value=5.0, value=1.0)
interval = st.selectbox("📊 Data Interval", options=["1m", "5m", "15m"], index=1)
start = st.button("🚀 Start Doctor Strategy")

# ========== Core Logic ==========
def fetch_data(symbol, interval):
    df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
    df.dropna(inplace=True)
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['VMA20'] = df['Volume'].rolling(window=20).mean()
    return df

if start and symbol:
    st.success("📡 Running Doctor Strategy... Signals will be sent to Telegram.")
    placeholder = st.empty()
    in_position = False
    entry_price = 0
    trailing_sl = 0
    qty = 0

    while True:
        try:
            df = fetch_data(symbol, interval)
            last = df.iloc[-1]
            prev = df.iloc[-2]

            price = last['Close']
            ema = last['EMA20']
            volume = last['Volume']
            vma = last['VMA20']

            # ========== Entry Logic ==========
            if not in_position:
                crossed_above = prev['Close'] < prev['EMA20'] and price > ema
                high_volume = volume > vma

                if crossed_above and high_volume:
                    entry_price = price
                    qty = int(capital / entry_price)
                    trailing_sl = round(entry_price * (1 - sl_percent / 100), 2)
                    in_position = True

                    st.success(f"📥 BUY @ ₹{entry_price}")
                    send_telegram_message(f"📥 <b>BUY SIGNAL - Doctor Strategy</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ₹{entry_price}\n<b>SL:</b> ₹{trailing_sl}\n<b>Qty:</b> {qty}")

            # ========== In Trade ==========
            elif in_position:
                # Trailing SL upward
                new_trailing_sl = round(price * (1 - sl_percent / 100), 2)
                if new_trailing_sl > trailing_sl:
                    trailing_sl = new_trailing_sl
                    send_telegram_message(f"🔁 <b>Trailing SL Updated</b>\n<b>New SL:</b> ₹{trailing_sl}")

                # Exit Condition
                if price < trailing_sl:
                    st.error(f"📤 SELL @ ₹{price} (SL Hit)")
                    send_telegram_message(f"📤 <b>SELL SIGNAL - SL Hit</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ₹{price}")
                    in_position = False
                    entry_price = 0
                    trailing_sl = 0

            # ========== Display ==========
            with placeholder.container():
                st.metric("📊 Live Price", f"₹{price:.2f}")
                st.metric("📈 EMA20", f"₹{ema:.2f}")
                st.metric("🔊 Volume", f"{volume:,.0f}")
                st.metric("📉 Trailing SL", f"₹{trailing_sl if in_position else '---'}")

            time.sleep(60)  # Wait before next check

        except Exception as e:
            st.error(f"❌ Error: {e}")
            send_telegram_message(f"❌ Error: {e}")
            break
