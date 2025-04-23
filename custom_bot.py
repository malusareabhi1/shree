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




if selected == "New Nifty Strategy":
    st.title("⚙️ Test New Nifty Strategy")
    st.sidebar.header("Trading Strategy Settings")

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

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Selected Stock:** {stock}")
    st.sidebar.markdown(f"**Order Type:** {order_type}")
    # Add an Action button
    run_strategy = st.button("🚀 Run Strategy")

    uploaded_file = st.file_uploader("📂 Upload CSV file", type="csv")
    
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Data loaded successfully")

        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        df['20_SMA'] = df['Close'].rolling(window=20).mean()
        df['Upper_Band'] = df['20_SMA'] + 2 * df['Close'].rolling(window=20).std()
        df['Lower_Band'] = df['20_SMA'] - 2 * df['Close'].rolling(window=20).std()

        st.dataframe(df.tail())

        trades = []
        capital = initial_capital
        position_open = False
        entry_price = 0
        trailing_stop = 0
        stop_loss_price = 0
        profit_target_price = 0
        entry_time = None
        reference_candle = None
        exit_reason = ""
        cumulative_pnl = []
        qty = lot_qty * 50  # assuming lot size of 50

        for idx, row in df.iterrows():
            current_time = idx.time()

            if start_time <= current_time <= stop_time:
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
                        if row['Close'] > entry_price * (1 + trailing_stop_pct):
                            trailing_stop = row['Close'] * (1 - trailing_stop_pct)
                        continue

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

                if row['Close'] > row['20_SMA'] and row['Close'] > row['Upper_Band']:
                    if reference_candle is not None and row['Close'] > reference_candle['Close']:
                        entry_price = row['Close']
                        stop_loss_price = entry_price * (1 - stop_loss_pct)
                        profit_target_price = entry_price * (1 + profit_target_pct)
                        trailing_stop = entry_price * (1 - trailing_stop_pct)
                        entry_time = idx
                        position_open = True
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
                continue

        final_capital = cumulative_pnl[-1] if cumulative_pnl else capital
        st.write(f"💰 Final Capital: ₹{final_capital:,.2f}")

        trade_df = pd.DataFrame(trades)

        if not trade_df.empty:
            st.subheader("📋 Trade Log")
            st.dataframe(trade_df)

            csv = trade_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Trade Log as CSV",
                data=csv,
                file_name='trade_log.csv',
                mime='text/csv',
            )

            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Candlesticks'
            )])

            for trade in trades:
                color = 'green' if trade['Action'] == 'BUY' else 'red'
                symbol = 'triangle-up' if trade['Action'] == 'BUY' else 'triangle-down'
                fig.add_trace(go.Scatter(
                    x=[trade['Time']],
                    y=[trade['Price']],
                    mode='markers',
                    marker=dict(symbol=symbol, color=color, size=10),
                    name=trade['Action']
                ))

            fig.update_layout(
                title="📉 Strategy Execution Chart",
                xaxis_title="Date",
                yaxis_title="Price (₹)",
                template="plotly_dark",
                hovermode="x unified"
            )
            st.plotly_chart(fig)

            trade_df['Cumulative Capital'] = trade_df['Capital'].ffill()
            pnl_fig = go.Figure()
            pnl_fig.add_trace(go.Scatter(
                x=trade_df['Time'],
                y=trade_df['Cumulative Capital'],
                mode='lines+markers',
                line=dict(color='gold', width=2),
                name='Cumulative Capital'
            ))
            pnl_fig.update_layout(
                title="📈 Cumulative Capital Over Time",
                xaxis_title="Date",
                yaxis_title="Capital (₹)",
                template="plotly_dark"
            )
            st.plotly_chart(pnl_fig)
