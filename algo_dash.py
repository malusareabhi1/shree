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
# Live Trading Section
if section == "Live Trading":
    st.subheader("🚀 Live Trading Control")
    def plot_candles_with_sma(df):
        df['20-SMA'] = df['price'].rolling(window=20).mean()
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["price"],
            name="Candlesticks"
        )])
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['20-SMA'],
            mode='lines',
            name='20-SMA',
            line=dict(color='orange', width=2)
        ))
        fig.update_layout(
            title="NIFTY 5‑Minute Candles with 20-SMA",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False
        )
        return fig

    def get_nifty_data():
        df = yf.download(tickers=symbol, interval=interval, period="2d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = df.index.tz_convert("Asia/Kolkata")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Date"}, inplace=True)
        for col in ["Open", "High", "Low", "Close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
        return df

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

    is_live = st.checkbox("Activate Live Trading")

    # Convert trade log to DataFrame, ensuring 'Side' column exists
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []

    trade_df = pd.DataFrame(st.session_state.trade_log)

    # Ensure required columns exist in the DataFrame
    if not trade_df.empty and "Side" in trade_df.columns:
        # Live Calculations
        trades_today = len(trade_df)
        total_pnl = trade_df.apply(lambda row: 100 if row["Side"] == "Buy" else -50, axis=1).sum()  # Example PnL logic
        wins = trade_df[trade_df["Side"] == "Buy"]  # Simplified: Buy = Win, Sell = Loss
        win_rate = (len(wins) / trades_today * 100) if trades_today > 0 else 0
    else:
        trades_today = 0
        total_pnl = 0
        win_rate = 0

    # Display live metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("🔢 Trades Today", f"{trades_today}")
    col2.metric("💰 Total PnL", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:+,.0f}")
    col3.metric("📊 Win Rate", f"{win_rate:.0f}%", delta="↑" if win_rate >= 50 else "↓")

    # Live Chart Section
    st.subheader("📉 Live Price Chart")
    #df = get_nifty_data()

    try:
        data = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        if isinstance(data.columns, pd.MultiIndex):  # This checks if the columns are a MultiIndex
            data.columns = data.columns.get_level_values(0)
                 # Ensure datetime index is timezone-aware in UTC and then convert to IST
            data.index = data.index.tz_convert("Asia/Kolkata")
        
        if not data.empty:
            df = data.reset_index()
            df["Datetime"] = pd.to_datetime(df["Datetime"])  # Ensure datetime
            df = df[["Datetime", "Close"]]
            df.columns = ["time", "price"]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["time"], y=df["price"], mode="lines", name=selected_symbol))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ No data received for selected symbol.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

   # st.write("Columns in df:", df.columns.tolist())

    if df.empty:
        st.warning("No data available for today’s 5‑min bars.")
    else:
        st.subheader("📊 Candlestick Chart")
        #st.plotly_chart(plot_candles_with_sma(df), use_container_width=True)

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

