import streamlit as st
import yfinance as yf

st.title("📈 Current NIFTY 50 Price")

# Nifty 50 index symbol on Yahoo Finance
symbol = "^NSEI"

try:
    # Fetch latest data (1d interval for today)
    data = yf.download(symbol, period="1d", interval="1m")
    
    if data.empty:
        st.error("❌ Could not fetch NIFTY 50 data.")
    else:
        # Get the most recent closing price
        current_price = data["Close"].iloc[-1]
        st.metric("NIFTY 50", f"{current_price:.2f} ₹")

except Exception as e:
    st.error(f"Error fetching data: {e}")
