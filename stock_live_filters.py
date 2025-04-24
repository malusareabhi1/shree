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

import plotly.graph_objects as go

def plot_candle_only(df, title="Candlestick Chart"):
    fig = go.Figure(data=[go.Candlestick(
        x=df['Datetime'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price',
        increasing_line_color='green',
        decreasing_line_color='red'
    )])

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        template="plotly_dark",  # Use dark theme, you can change it
        height=700
    )

    fig.show()




#import datetime
#import streamlit as st
#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if run_strategy:
    st.subheader(f"📥 Loading {stock} - {frame_interval} data for last 2 days...")

    # Mapping Streamlit frame_interval to yfinance interval
    interval_map = {
        "5m": "5m",
        "15m": "15m",
        "1h": "60m",
        "1d": "1d"
    }
    yf_interval = interval_map.get(frame_interval, "5m")

    try:
        # Fetch last 2 days of selected intraday frame
        df = yf.download(
            tickers=stock,
            period="2d",
            interval=yf_interval,
            progress=False
        )
            #df.index = pd.to_datetime(df.index)
        print(df.columns)
        print(df.head())    
        if df.index.tz is None:
            df = df.tz_localize("UTC").tz_convert("Asia/Kolkata")
        else:
            df = df.tz_convert("Asia/Kolkata")
    
        df = df.between_time("09:15", "15:30")



            
        

        if df.empty:
            st.error("⚠️ No data found. Please try another stock or timeframe.")
        else:
            df = df.between_time("09:15", "15:30")   
            df = df.dropna().copy()
            df.index = df.index.tz_localize(None)  # Remove timezone for compatibility
            st.success(f"✅ Loaded {len(df)} rows of data.")
            st.dataframe(df.tail())  # Show last few rows

            
       

            # You can now call your strategy, chart, or signal logic here
        plot_candle_only(df)

    except Exception as e:
        st.error(f"❌ Error while loading data: {e}")

#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------




