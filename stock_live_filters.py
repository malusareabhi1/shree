#
import plotly.express as px
import plotly.graph_objects as go
import os
import streamlit as st
import yfinance as yf
import pandas as pd
import time
import requests
import datetime
from dotenv import load_dotenv
# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="📈 Nifty EMA20 Breakout", layout="wide")
st.title("📊 Nifty 5-min EMA20 + Volume Breakout Monitor")

# ─── LOAD ENVIRONMENT VARIABLES ───────────────────────────────────────────────
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Sidebar controls
stock = st.sidebar.selectbox("Select Stock", [ "^NSEI","^NSEBANK", "ADANIENT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
        "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
        "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFC.NS",
        "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
        "INDUSINDBK.NS", "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS",
        "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS",
        "SBIN.NS", "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS",
        "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"])
chart_type = st.sidebar.selectbox("Select Chart Type", ["Candlestick", "Line", "OHLC"])
initial_capital = st.sidebar.number_input("Initial Capital (₹)", min_value=1000, value=100000, step=1000)
daily_trade_limit = st.sidebar.number_input("Daily Trade Limit", min_value=1, value=5)
start_time = st.sidebar.time_input("Trade Start Time", value=datetime.time(9, 30))
stop_time = st.sidebar.time_input("Trade Stop Time", value=datetime.time(14, 30))
lot_qty = st.sidebar.number_input("Lot Quantity", min_value=1, value=1)

frame_interval = st.sidebar.selectbox("Select Time Frame", ["5m", "15m", "1h", "1d"])
order_type = st.sidebar.selectbox("Order Type", ["Market", "Limit"])

stop_loss_pct = st.sidebar.slider("Stop Loss (%)", min_value=0.5, max_value=10.0, value=1.0) / 100
profit_target_pct = st.sidebar.slider("Profit Target (%)", min_value=0.5, max_value=10.0, value=2.0) / 100
trailing_stop_pct = st.sidebar.slider("Trailing Stop Loss (%)", min_value=0.1, max_value=5.0, value=0.5) / 100
enable_time_exit = st.sidebar.checkbox("Enable Time-Based Exit", value=True)
exit_minutes = st.sidebar.slider("Exit After (Minutes)", min_value=1, max_value=60, value=10)

run_strategy = st.sidebar.button("🚀 Run Strategy")

# ─── TELEGRAM ALERT FUNCTION ──────────────────────────────────────────────────
def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")




#import datetime
#import streamlit as st
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if run_strategy:
    with st.spinner("Fetching data..."):
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=2)

        try:
            df = yf.download(stock, start=start_date, end=end_date, interval=frame_interval, progress=False)

            if df.empty:
                st.warning("No data found for the selected stock and timeframe.")
            else:
                st.success(f"Fetched {len(df)} rows of data for {stock}.")
                st.dataframe(df.tail(10))  # Show last 10 rows

        except Exception as e:
            st.error(f"Data fetch error: {e}")
#st.write(df.index())
# Plot chart
st.subheader(f"{stock} - {frame_interval} Chart")
st.subheader("🕯️  5-Min Candle Chart with 20 EMA")
    
    # Plot the candlestick chart with 20 EMA
fig = go.Figure(data=[
        go.Candlestick(
        x=df_today.index,
        open=df_today["Open"],
        high=df_today["High"],
        low=df_today["Low"],
        close=df_today["Close"],
        increasing_line_color="green",
        decreasing_line_color="red",
        name="Candles"
        ),
        go.Scatter(
            x=df_today.index,
            y=df_today['EMA20'],
            mode='lines',
            line=dict(color='blue', width=2),
            name='20 EMA'
        )
    ])
fig.update_layout(
         xaxis_rangeslider_visible=False,
         xaxis_title="Time",
         yaxis_title="Price (₹)",
         template="plotly_dark",
         height=500
     )
st.plotly_chart(fig, use_container_width=True)


            
            



   
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




