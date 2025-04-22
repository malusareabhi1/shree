import requests
import streamlit as st

def get_binance_price(symbol="BTCUSDT"):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}"
        response = requests.get(url, timeout=5)
        data = response.json()

        # Check if the response has 'price'
        if 'price' not in data:
            st.error(f"⚠️ Response doesn't contain 'price': {data}")
            return None

        return float(data['price'])
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Request error: {e}")
    except ValueError as e:
        st.error(f"❌ Parsing error: {e}")
    except Exception as e:
        st.error(f"❌ Unknown error: {e}")
    return None

st.title("🚀 Live Crypto Price")

symbol = st.selectbox("Choose Crypto Symbol", ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"])
price = get_binance_price(symbol)

if price:
    st.metric(label=f"{symbol} Price", value=f"${price:,.2f}")
