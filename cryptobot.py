import streamlit as st
import requests
import time

st.set_page_config(page_title="Crypto Algo Trading", layout="centered")

# ====== Telegram Setup ======
bot_token = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
chat_id = "1320205499"
def send_telegram(msg):
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML"
    }
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=payload)

# ====== Binance Price Fetch ======
def get_price(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        response = requests.get(url).json()
        return float(response['price'])
    except:
        return None

# ====== UI ======
st.title("💹 Crypto Algo Trading (Paper Mode)")

symbol = st.selectbox("Select Crypto", ["BTCUSDT", "ETHUSDT", "BNBUSDT"])
capital = st.number_input("💰 Capital (USD)", value=500.0)
stop_loss_pct = st.slider("🔻 Stop Loss (%)", 0.5, 5.0, 2.0)
trailing_step_pct = st.slider("📈 Trailing Step (%)", 0.5, 5.0, 1.0)

start = st.button("🚀 Start Strategy")
stop = st.button("🛑 Stop Strategy")

# ====== Session State for Control ======
if 'running' not in st.session_state:
    st.session_state.running = False

if start:
    st.session_state.running = True
if stop:
    st.session_state.running = False

# ====== Strategy Logic ======
if st.session_state.running:
    st.success(f"📡 Running Doctor Strategy on {symbol}...")

    qty = 0
    entry_price = None
    trailing_sl = None
    live_placeholder = st.empty()

    while st.session_state.running:
        price = get_price(symbol)
        if price is None:
            st.error("❌ Failed to fetch price")
            break

        if entry_price is None:
            entry_price = price
            qty = round(capital / entry_price, 5)
            trailing_sl = entry_price * (1 - stop_loss_pct / 100)
            send_telegram(f"📥 <b>PAPER BUY</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ${entry_price:.2f}\n<b>Qty:</b> {qty}")
        elif price >= entry_price * (1 + trailing_step_pct / 100):
            new_sl = price * (1 - stop_loss_pct / 100)
            if new_sl > trailing_sl:
                trailing_sl = new_sl
                send_telegram(f"🔁 <b>Trailing SL Updated</b>\n<b>New SL:</b> ${trailing_sl:.2f}")
        elif price <= trailing_sl:
            send_telegram(f"📤 <b>PAPER SELL</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ${price:.2f}\n<b>Reason:</b> SL Hit")
            st.session_state.running = False
            break

        with live_placeholder.container():
            st.metric("💸 Live Price", f"${price:.2f}")
            st.metric("Entry", f"${entry_price:.2f}")
            st.metric("Trailing SL", f"${trailing_sl:.2f}")
            st.metric("Qty", qty)

        time.sleep(10)

    st.warning("⏹️ Strategy stopped.")
