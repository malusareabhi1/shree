import requests
import streamlit as st

def get_coingecko_price(symbol="bitcoin"):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        data = response.json()

        if symbol not in data or 'usd' not in data[symbol]:
            st.error(f"⚠️ Response error: {data}")
            return None

        return float(data[symbol]['usd'])

    except Exception as e:
        st.error(f"❌ Error fetching price: {e}")
        return None

st.title("🚀 Live Crypto Price")

symbol = st.selectbox("Choose Crypto Symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"])
price = get_binance_price(symbol)

if price:
    st.metric(label=f"{symbol} Price", value=f"${price:,.2f}")
