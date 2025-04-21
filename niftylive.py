import streamlit as st
import yfinance as yf

# 🛠️ This MUST be the first Streamlit command!
st.set_page_config(page_title="📊 NIFTY 50 Live Chart", layout="wide")

st.title("📈 NIFTY 50 Live Chart (1-min)")

if st.button("🔄 Refresh Data"):
    ticker = "^NSEI"
    nifty = yf.Ticker(ticker)
    data = nifty.history(period="1d", interval="1m")

    if not data.empty:
        live_price = data["Close"].iloc[-1]
        st.metric(label="NIFTY 50 Live Price", value=f"{live_price:.2f}")
        st.line_chart(data["Close"])
    else:
        st.warning("⚠️ Failed to fetch data.")
