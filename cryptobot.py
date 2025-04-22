import requests
import streamlit as st

def get_binance_price(symbol="BTCUSDT"):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        data = response.json()
        return float(data["price"])
    except Exception as e:
        st.error(f"❌ Failed to fetch price: {e}")
        return None

# Example usage in Streamlit
st.title("💸 Live Crypto Price")

symbol = st.selectbox("Select Symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"])
price = get_binance_price(symbol)

if price:
    st.metric(f"{symbol} Price", f"${price:,.2f}")

import time

entry_price = None
trailing_sl = None
qty = 0.01

while True:
    price = get_binance_price("BTCUSDT")
    if price is None:
        break

    if entry_price is None:
        entry_price = price
        trailing_sl = price - 50
        send_telegram(f"📥 <b>BUY BTC</b> at ${entry_price}")
    elif price >= entry_price + 100:
        trailing_sl = price - 50
        send_telegram(f"🔁 <b>Trailing SL Updated</b>: ${trailing_sl}")
    elif price <= trailing_sl:
        send_telegram(f"📤 <b>SELL BTC</b> at ${price} (SL Hit)")
        break

    time.sleep(10)

