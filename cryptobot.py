import requests

def get_coingecko_price(symbol="bitcoin"):
    try:
        # CoinGecko uses lowercase IDs like "bitcoin", "ethereum", etc.
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": symbol,
            "vs_currencies": "usd"
        }

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
