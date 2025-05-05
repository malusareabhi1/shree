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
        st.metric("NIFTY 50", f"{current_price:.2f} ₹")

except Exception as e:
    st.error(f"Error fetching data: {e}")
