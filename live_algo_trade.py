import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import random
import requests
from kiteconnect import KiteConnect
import time
import threading
import datetime
from datetime import datetime, timedelta
import os
import pytz
import ta  # Required for trend calculation (ensure installed)


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Strategy Settings")

st.sidebar.title("📋 Navigation")
selected = st.sidebar.selectbox("Choose a section", [
    "Home",
    "Live Algo Trading",
    "Backtest Strategy",
    "View Logs",
    "Settings"
])

telegram_alert = st.sidebar.checkbox("📣 Send Telegram Alerts", value=True)

st.sidebar.markdown("---")
st.sidebar.success("🟢 Strategy Status: Active")
st.sidebar.markdown("⏱️ Updates every 30 seconds")


if selected == "Live Algo Trading":
    st.title("🤖 Live Algo Trading   ")
    from dotenv import load_dotenv

    # ─── LOAD ENVIRONMENT VARIABLES ───────────────────────────────────────────────
    load_dotenv()
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # ─── TELEGRAM ALERT FUNCTION ──────────────────────────────────────────────────
    def send_telegram(msg: str):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            st.error(f"Telegram Error: {e}")
    
    # ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
    #st.set_page_config(page_title="📈 Nifty EMA20 Breakout", layout="wide")
    #st.title("📊 Nifty 5-min EMA20 + Volume Breakout Monitor")
    
    # ─── STRATEGY TEST STARTED ─────────────────────────────────────────────────────
    start_msg = "🟢 Strategy Test Started"
    st.info(start_msg)
    #send_telegram(start_msg)
    
    # ─── FETCH DATA ───────────────────────────────────────────────────────────────
    @st.cache_data(ttl=60)
    def fetch_data(ticker: str) -> pd.DataFrame:
        df = yf.download(ticker, interval="5m", period="5d", progress=False)
        df.index = pd.to_datetime(df.index)
    
        if df.index.tz is None:
            df = df.tz_localize("UTC").tz_convert("Asia/Kolkata")
        else:
            df = df.tz_convert("Asia/Kolkata")
    
        df = df.between_time("09:15", "15:30")
    
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["VMA20"] = df["Volume"].rolling(20).mean()
        return df
    
    symbol = "^NSEI"
    df = fetch_data(symbol)
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # ─── MARKET OPEN/CLOSE MESSAGE ────────────────────────────────────────────────
    now = latest.name
    if now.hour == 9 and now.minute == 15:
        market_msg = "📈 Market Opened at 09:15 But My Doctor Stratergy will Start 09:30 "
        st.success(market_msg)
        send_telegram(market_msg)

    if now.hour == 14 and now.minute == 30:
        market_close_msg = "📉 Doctor Stratergy will  not take Trade after 02:30"
        st.warning(market_close_msg)
        send_telegram(market_close_msg)

     

    if now.hour == 15 and now.minute == 30:
        market_close_msg = "📉 Market Closed at 15:30 Bye ! See you Tomorrow 9:30"
        st.warning(market_close_msg)
        send_telegram(market_close_msg)



    # ─── STRATEGY LOGIC ───────────────────────────────────────────────────────────
   # Initialize
st.title("📈 Live Doctor Strategy - NIFTY 5m")
telegram_token = 'your_token'
telegram_chat_id = 'your_chat_id'
symbol_token = '256265'  # NIFTY index
capital = 100000
qty = 50
iv_threshold = 16
active_trade = None
trade_log = []

# Assuming kite is your logged-in KiteConnect object
def get_live_5min_data(kite, instrument_token, days=1):
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    data = kite.historical_data(instrument_token, from_date, to_date, "5minute")
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['date'])
    return df[['datetime', 'open', 'high', 'low', 'close']]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    requests.post(url, data={"chat_id": telegram_chat_id, "text": msg})

# Main Loop
placeholder = st.empty()
run_button = st.button("Start Live Algo")

if run_button:
    while True:
        try:
            df = get_live_5min_data(kite, int(symbol_token), days=2)

            # Technical Indicators
            df['sma_20'] = df['close'].rolling(20).mean()
            df['upper_band'] = df['sma_20'] + 2 * df['close'].rolling(20).std()
            df['lower_band'] = df['sma_20'] - 2 * df['close'].rolling(20).std()

            # Signal Logic
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            now = datetime.now().time()

            condition_entry = (
                prev['close'] < prev['upper_band']
                and latest['close'] > latest['upper_band']
                and latest['close'] > latest['sma_20']
                and iv_threshold > 15  # You could make this dynamic
                and datetime.strptime("09:30:00", "%H:%M:%S").time() < now < datetime.strptime("14:30:00", "%H:%M:%S").time()
            )

            if active_trade is None and condition_entry:
                entry_price = latest['close']
                stop_loss = entry_price * 0.995
                target = entry_price * 1.02
                active_trade = {
                    'Entry_Time': latest['datetime'],
                    'Entry_Price': entry_price,
                    'Stop_Loss': stop_loss,
                    'Target': target,
                    'Status': 'OPEN'
                }
                msg = f"🚀 LONG ENTRY\nNIFTY @ {entry_price}\nSL: {stop_loss:.2f}, Target: {target:.2f}"
                send_telegram(msg)

            # Check Exit Conditions
            if active_trade:
                current_price = latest['close']
                hit_sl = current_price <= active_trade['Stop_Loss']
                hit_target = current_price >= active_trade['Target']
                time_exit = now >= datetime.strptime("15:20:00", "%H:%M:%S").time()

                if hit_sl or hit_target or time_exit:
                    exit_price = current_price
                    pnl = (exit_price - active_trade['Entry_Price']) * qty
                    trade_log.append({
                        **active_trade,
                        'Exit_Time': latest['datetime'],
                        'Exit_Price': exit_price,
                        'PnL': pnl
                    })
                    result = "TARGET HIT" if hit_target else "STOP LOSS" if hit_sl else "TIME EXIT"
                    send_telegram(f"💼 EXIT ({result}) @ {exit_price:.2f}, PnL: ₹{pnl:.2f}")
                    active_trade = None

            # UI Updates
            with placeholder.container():
                st.subheader("🔁 Live Data")
                st.write(df.tail(3))

                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df['datetime'], open=df['open'], high=df['high'],
                                             low=df['low'], close=df['close'], name='Candles'))
                fig.add_trace(go.Scatter(x=df['datetime'], y=df['upper_band'], name='Upper Band', line=dict(color='red')))
                fig.add_trace(go.Scatter(x=df['datetime'], y=df['lower_band'], name='Lower Band', line=dict(color='green')))
                fig.add_trace(go.Scatter(x=df['datetime'], y=df['sma_20'], name='SMA 20', line=dict(color='blue')))

                if active_trade:
                    fig.add_trace(go.Scatter(x=[active_trade['Entry_Time']], y=[active_trade['Entry_Price']],
                                             mode='markers', name='Entry', marker=dict(color='yellow', size=12)))

                st.plotly_chart(fig, use_container_width=True)

                if trade_log:
                    st.subheader("📊 Trade Log")
                    st.dataframe(pd.DataFrame(trade_log))

            time.sleep(60)  # Wait 1 minute
        except Exception as e:
            st.error(f"Error: {str(e)}")
            time.sleep(60)



        
        send_telegram(msg)

    
    
    # ─── DISPLAY ──────────────────────────────────────────────────────────────────
    #st.subheader("📊 Last 5 Candles")
    #st.dataframe(df.tail(5))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔹 Close", f"₹{latest['Close']:.2f}")
    col2.metric("🔸 EMA20", f"₹{latest['EMA20']:.2f}")
    col3.metric("📌 Signal", signal)
    #---------------------------------------------------------------------------------------
    import plotly.graph_objects as go
    from datetime import datetime
    
    # ─── filter for today's date ──────────────────────────────────────
    # assume df.index is timezone-aware in IST
    today = datetime.now().astimezone(df.index.tz).date()
    df_today = df[df.index.date == today]
    
    # Calculate 20 EMA
    df_today['EMA20'] = df_today['Close'].ewm(span=20, adjust=False).mean()
    
    st.subheader("🕯️ Today's 5-Min Candle Chart with 20 EMA")
    
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
    
    #---------------------------------------------------------------------------------------
    #st.subheader("📈 Price vs EMA20")
    #st.line_chart(df[["Close", "EMA20"]])
    
    # ─── STRATEGY TEST STOPPED ────────────────────────────────────────────────────
    stop_msg = "🔴 Strategy Test Ended (for current run)"
    st.info(stop_msg)
    #send_telegram(stop_msg)
    
    # ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
    st.markdown("⏱️ Auto-refresh every 30 seconds")
    #with st.spinner("⏳ Refreshing in 30 seconds..."):
    time.sleep(30)
    st.rerun()
