import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
#from utils import generate_mock_data
import random
import requests
from kiteconnect import KiteConnect
import time
import threading
import datetime

import os
import pytz  # ✅ Add this



# Global kite object placeholder
if 'kite' not in st.session_state:
    st.session_state.kite = None
# Page configuration
st.set_page_config(layout="wide", page_title="Trade Strategy Dashboard")
    
# Sidebar navigation
with st.sidebar:
    selected = option_menu(
    menu_title="ALGO BOT Trade ",
    options=[
        "Dashboard", "Get Stock Data", "Doctor Strategy","Doctor1.0 Strategy","Doctor2.0 Strategy","Doctor3.0 Strategy", "Swing Trade Strategy","New Nifty Strategy",
        "Intraday Stock Finder", "Trade Log", "Account Info", "Candle Chart", "Strategy Detail","Strategy2.0 Detail", "Project Detail", "KITE API", "API","Alpha Vantage API","Live Algo Trading"
    ],
    icons=[
        "bar-chart", "search", "cpu","cpu", "cpu","cpu","cpu", "arrow-repeat",
        "search", "clipboard-data", "wallet2", "graph-up", "info-circle", "file-earmark","file-earmark", "code-slash", "code-slash", "code-slash","journal-text"
    ],
    menu_icon="cast",
    default_index=0,
)   

# Main area rendering
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .card {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            padding: 20px;
            margin: 10px 0;
        }
        .card-title {
            font-size: 18px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)




#from datetime import timedelta  # ✅ Add this import

if selected == "New Nifty Strategy":
    st.title("⚙️ Test New Nifty Strategy")
    st.sidebar.header("Trading Strategy Settings")

    # Sidebar controls
    chart_type = st.sidebar.selectbox("Select Chart Type", ["Candlestick", "Line", "OHLC"])
    initial_capital = st.sidebar.number_input("Initial Capital (₹)", min_value=1000, value=100000, step=1000)
    daily_trade_limit = st.sidebar.number_input("Daily Trade Limit", min_value=1, value=5)
    start_time = st.sidebar.time_input("Trade Start Time", value=datetime.time(9, 30))
    stop_time = st.sidebar.time_input("Trade Stop Time", value=datetime.time(14, 30))
    lot_qty = st.sidebar.number_input("Lot Quantity", min_value=1, value=1)
    stock = st.sidebar.selectbox("Select Stock", ["RELIANCE", "INFY", "HDFCBANK", "TCS", "ICICIBANK", "NIFTY", "BANKNIFTY"])
    frame_interval = st.sidebar.selectbox("Select Time Frame", ["5m", "15m", "1h", "1d"])
    order_type = st.sidebar.selectbox("Order Type", ["Market", "Limit"])

    stop_loss_pct = st.sidebar.slider("Stop Loss (%)", min_value=0.5, max_value=10.0, value=1.0) / 100
    profit_target_pct = st.sidebar.slider("Profit Target (%)", min_value=0.5, max_value=10.0, value=2.0) / 100
    trailing_stop_pct = st.sidebar.slider("Trailing Stop Loss (%)", min_value=0.1, max_value=5.0, value=0.5) / 100
    enable_time_exit = st.sidebar.checkbox("Enable Time-Based Exit", value=True)
    exit_minutes = st.sidebar.slider("Exit After (Minutes)", min_value=1, max_value=60, value=10)

    run_strategy = st.button("🚀 Run Strategy")

    uploaded_file = st.file_uploader("📂 Upload CSV file", type="csv")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Data loaded successfully")

        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # Calculate indicators
        df['20_SMA'] = df['Close'].rolling(window=20).mean()
        df['Upper_Band'] = df['20_SMA'] + 2 * df['Close'].rolling(window=20).std()
        df['Lower_Band'] = df['20_SMA'] - 2 * df['Close'].rolling(window=20).std()

        st.dataframe(df.tail())

        # Initialize trade variables
        trades = []
        capital = initial_capital
        position_open = False
        entry_price = 0
        trailing_stop = 0
        stop_loss_price = 0
        profit_target_price = 0
        entry_time = None
        reference_candle = None
        qty = lot_qty * 50  # Assuming lot size of 50
        cumulative_pnl = []
        trade_count = 0

        for idx, row in df.iterrows():
            current_time = idx.time()

            # Only trade in time range
            if start_time <= current_time <= stop_time:
                # Exit logic
                if position_open:
                    if row['Close'] <= stop_loss_price:
                        exit_reason = "Stop Loss Hit"
                    elif row['Close'] >= profit_target_price:
                        exit_reason = "Profit Target Hit"
                    elif row['Close'] < trailing_stop and trailing_stop > 0:
                        exit_reason = "Trailing Stop Hit"
                    elif enable_time_exit and (idx - entry_time) > timedelta(minutes=exit_minutes):
                        exit_reason = "Time-Based Exit"
                    else:
                        # Update trailing stop
                        if row['Close'] > entry_price * (1 + trailing_stop_pct):
                            trailing_stop = row['Close'] * (1 - trailing_stop_pct)
                        continue  # Continue holding

                    # Record exit
                    pnl = qty * (row['Close'] - entry_price)
                    capital += pnl
                    cumulative_pnl.append(capital)
                    trades.append({
                        'Action': 'SELL',
                        'Price': row['Close'],
                        'Exit Reason': exit_reason,
                        'Time': idx,
                        'Capital': capital,
                        'PnL': pnl
                    })
                    position_open = False
                    trailing_stop = 0
                    continue

                # Entry logic
                if row['Close'] > row['20_SMA'] and row['Close'] > row['Upper_Band']:
                    if reference_candle is not None and row['Close'] > reference_candle['Close'] and trade_count < daily_trade_limit:
                        entry_price = row['Close']
                        stop_loss_price = entry_price * (1 - stop_loss_pct)
                        profit_target_price = entry_price * (1 + profit_target_pct)
                        trailing_stop = entry_price * (1 - trailing_stop_pct)
                        entry_time = idx
                        position_open = True
                        trade_count += 1
                        trades.append({
                            'Action': 'BUY',
                            'Price': entry_price,
                            'Time': idx,
                            'Capital': capital,
                            'PnL': 0,
                            'Exit Reason': ""
                        })
                    reference_candle = row
                else:
                    reference_candle = None

        # Final results
        if trades:
            st.subheader("📊 Trade Summary")
            st.dataframe(pd.DataFrame(trades))

            # PnL Line Chart
            st.subheader("📈 Capital Over Time")
            fig = px.line(x=list(range(len(cumulative_pnl))), y=cumulative_pnl, labels={'x': 'Trade', 'y': 'Capital'})
            st.plotly_chart(fig, use_container_width=True)

            # Candlestick Chart with Markers
            st.subheader("🕯️ Candlestick Chart with Entry/Exit")
            fig2 = go.Figure(data=[go.Candlestick(x=df.index,
                                                  open=df['Open'],
                                                  high=df['High'],
                                                  low=df['Low'],
                                                  close=df['Close'])])
            for t in trades:
                color = "green" if t['Action'] == "BUY" else "red"
                fig2.add_trace(go.Scatter(x=[t['Time']], y=[t['Price']],
                                          mode='markers+text',
                                          marker=dict(color=color, size=10),
                                          name=t['Action'],
                                          text=[t['Action']],
                                          textposition='top center'))
            st.plotly_chart(fig2, use_container_width=True)
