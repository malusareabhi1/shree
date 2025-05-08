import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime

import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
#from utils import generate_mock_data
import random
import requests
from kiteconnect import KiteConnect
import time
import threading
#import datetime
from datetime import datetime, timedelta
import os
import pytz  # ✅ Add this for details ssfsdfsdf 
from streamlit_autorefresh import st_autorefresh

# Page config
st.set_page_config(page_title="Algo Trading Dashboard", layout="wide")

# Sidebar
st.sidebar.title("📈 Algo Dashboard")
section = st.sidebar.radio("Navigate", ["Live Trading", "Backtest", "Trade Log", "Settings"])

# Dummy trade log for display
trade_log_df = pd.DataFrame(columns=["Time", "Symbol", "Side", "Qty", "Price", "Status"])

# Header
st.title("💹 Algo Trading Dashboard")

# Live Trading Section
if section == "Live Trading":
    st.subheader("🚀 Live Trading Control")

    strategy = st.selectbox("Select Strategy", ["Doctor Strategy", "ORB", "Momentum", "Mean Reversion"])
    selected_symbol = st.selectbox("Select Live Symbol", ["NIFTY 50", "RELIANCE", "INFY", "TCS", "HDFC BANK", "ICICI BANK"])
    
    symbol_map = {
        "NIFTY 50": "^NSEI",
        "RELIANCE": "RELIANCE.NS",
        "INFY": "INFY.NS",
        "TCS": "TCS.NS",
        "HDFC BANK": "HDFCBANK.NS",
        "ICICI BANK": "ICICIBANK.NS"
    }
    ticker = symbol_map[selected_symbol]

    is_live = st.toggle("Activate Live Trading")

    col1, col2, col3 = st.columns(3)
    col1.metric("🔢 Trades Today", "14", "+3")
    col2.metric("💰 Total PnL", "₹12,350", "+₹1,200")
    col3.metric("📊 Win Rate", "68%", "↑")

    # Live Chart Section
    st.subheader("📉 Live Price Chart")

    try:
        import yfinance as yf
        data = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        if not data.empty:
            df = data.reset_index()[["Datetime", "Close"]]
            df.columns = ["time", "price"]
            df.index = df.index.tz_convert("Asia/Kolkata")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["time"], y=df["price"], mode="lines", name=selected_symbol))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No data received for selected symbol.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []

    if is_live and not data.empty:
        st.success("Live trading is active")
        status_placeholder = st.empty()
        log_placeholder = st.empty()

        for i in range(10):  # Simulated 10 updates
            live_price = round(df['price'].iloc[-1] + np.random.randn(), 2)
            current_time = pd.Timestamp.now().strftime("%H:%M:%S")

            # Simple signal logic
            signal = "Hold"
            if live_price > df['price'].iloc[-1] + 2:
                signal = "Buy"
            elif live_price < df['price'].iloc[-1] - 2:
                signal = "Sell"

            status_placeholder.markdown(f"### 📢 Signal: **{signal}** at ₹{live_price} ({current_time})")

            if signal in ["Buy", "Sell"]:
                st.session_state.trade_log.append({
                    "Time": current_time,
                    "Symbol": selected_symbol,
                    "Side": signal,
                    "Qty": 50,
                    "Price": live_price,
                    "Status": "Executed"
                })

            log_df = pd.DataFrame(st.session_state.trade_log)
            log_placeholder.dataframe(log_df, use_container_width=True)

            time.sleep(2)

    st.subheader("📘 Trade Log")
    log_df = pd.DataFrame(st.session_state.trade_log)
    st.dataframe(log_df, use_container_width=True)
    st.download_button("Download Log", log_df.to_csv(index=False).encode(), "trade_log.csv")

    if st.button("🛑 Stop Trading"):
        st.warning("Trading stopped manually.")

# Backtest Section
elif section == "Backtest":
    st.subheader("🧪 Backtest Strategy")
    st.info("Upload your historical data and test your strategy here.")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Data preview:")
        st.dataframe(df.head())

# Trade Log Section
elif section == "Trade Log":
    st.subheader("📋 All Trades History")
    # Load from file or DB
    st.dataframe(trade_log_df)

# Settings Section
elif section == "Settings":
    st.subheader("⚙️ API & Config Settings")
    api_key = st.text_input("Enter Broker API Key", type="password")
    secret_key = st.text_input("Enter API Secret", type="password")
    telegram_token = st.text_input("Telegram Bot Token", type="password")
    if st.button("Save Settings"):
        st.success("Settings saved securely.")

