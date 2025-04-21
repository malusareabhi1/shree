import streamlit as st
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# Autorefresh every 60 seconds (60000 ms)
st_autorefresh(interval=60000, key="refresh")

st.set_page_config(page_title="📊 NIFTY 50 Live Chart", layout="wide")

st.title("📈 NIFTY 50 Live Chart (1-min)")

# Fetch live data from Yahoo Finance
ticker = "^NSEI"
nifty = yf.Ticker(ticker)
data = nifty.history(period="1d", interval="1m")

# Get the latest price
if not data.empty:
    live_price = data["Close"].iloc[-1]
    st.metric(label="NIFTY 50 Live Price", value=f"{live_price:.2f}")
    st.line_chart(data["Close"])
else:
    st.warning("⚠️ Failed to fetch data. Please check your internet connection or try again later.")
