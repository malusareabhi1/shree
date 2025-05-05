import streamlit as st
import yfinance as yf

st.title("📈 Current NIFTY 50 Price")

# Yahoo Finance symbol for NIFTY 50 index
symbol = "^NSEI"

try:
    # Fetch intraday data for today
    data = yf.download(symbol, period="1d", interval="1m")

    if data.empty:
        st.error("❌ Failed to fetch NIFTY 50 data.")
    else:
        # Safely get the latest close price as float
        current_price = float(data["Close"].dropna().iloc[-1])
        # Day high
        day_high = float(data["High"].max())
        day_low = float(data["Low"].min())

        # Display metrics
        st.metric("🔹 Current Price", f"{current_price:.2f} ")
        st.metric("🔺 Day High", f"{day_high:.2f} ")
        col3.metric("🔻 Day Low", f"{day_low:.2f} ")

except Exception as e:
    st.error(f"⚠️ Error fetching data: {e}")
