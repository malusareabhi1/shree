import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime

# ========== Telegram Config ==========
TELEGRAM_TOKEN = "7887944907:AAHyOPITLm8d2SzKPtnwxnLsm6s0LfPm6FI"
#TELEGRAM_TOKEN = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
#CHAT_ID = "1320205499"
CHAT_ID = "1320205499"
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# ========== CoinGecko API ==========
def get_coingecko_price(symbol="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": symbol, "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if symbol in data and "usd" in data[symbol]:
            return float(data[symbol]["usd"])
        else:
            st.error(f"⚠️ Response error: {data}")
            return None
    except Exception as e:
        st.error(f"❌ Error fetching price: {e}")
        return None

# ========== Streamlit UI ==========
st.title("🤖 Crypto Algo Trading (Doctor Strategy 1.0)")
st.markdown("This is a **paper trading bot** running live on CoinGecko data with <b>Doctor Strategy</b> logic.", unsafe_allow_html=True)

symbol_map = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "Ripple": "ripple"
}

selected_name = st.selectbox("Choose Crypto", list(symbol_map.keys()))
symbol_id = symbol_map[selected_name]
capital = st.number_input("Capital Allocation (USD)", value=500.0)
qty = st.number_input("Quantity to Trade", value=1.0)
start = st.button("🚀 Start Doctor Strategy")
stop_signal = st.checkbox("🛑 Stop Bot")

# ========== Trading Logic ==========
if start:
    trade_log = []
    entry_price = None
    trailing_sl = None

    placeholder = st.empty()

    while not stop_signal:
        price = get_coingecko_price(symbol_id)
        current_time = datetime.now().strftime("%H:%M:%S")

        if price is None:
            time.sleep(5)
            continue

        # Entry condition
        if entry_price is None:
            entry_price = price
            trailing_sl = entry_price - 5
            send_telegram(f"📥 <b>Paper BUY</b>\n<b>Crypto:</b> {selected_name}\n<b>Price:</b> ${entry_price}\n<b>Qty:</b> {qty}")
            trade_log.append(["BUY", entry_price, qty, current_time, 0])
            st.success(f"📥 Buy executed at ${entry_price}")
        
        elif price >= entry_price + 5:
            trailing_sl = price - 5
            send_telegram(f"🔁 <b>Trailing SL Moved</b>\n<b>New SL:</b> ${trailing_sl}")

        elif price <= trailing_sl:
            pnl = round((price - entry_price) * qty, 2)
            send_telegram(f"📤 <b>Paper SELL</b>\n<b>Crypto:</b> {selected_name}\n<b>Exit:</b> ${price}\n<b>PnL:</b> ${pnl}")
            trade_log.append(["SELL", price, qty, current_time, pnl])
            st.error(f"📤 Sell executed at ${price} | PnL: ${pnl}")
            break  # Exit loop after trade

        # Live Display
        with placeholder.container():
            st.metric("Live Price", f"${price}")
            st.metric("Entry Price", f"${entry_price}")
            st.metric("Trailing SL", f"${trailing_sl}")
            st.metric("Qty", qty)
            st.write("⏱️", current_time)

        time.sleep(10)

    # Show log
    if trade_log:
        df_log = pd.DataFrame(trade_log, columns=["Action", "Price", "Qty", "Time", "PnL"])
        st.subheader("📒 Trade Log")
        st.dataframe(df_log)
        csv = df_log.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Trade Log", csv, "crypto_trade_log.csv", "text/csv")
