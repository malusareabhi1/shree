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
    def check_doctor_strategy_entry(df, current_iv):
        """
        Checks for a valid entry signal using Doctor Strategy conditions.
        
        Parameters:
        - df: DataFrame with live 5-min OHLC data (should be at least 5-10 recent candles)
        - current_iv: Live Implied Volatility (%) of the index
    
        Returns:
        - signal: Dict with 'signal' (True/False), 'entry_price', 'sl', 'target', 'reference_candle', 'entry_time'
        """
        df = df.copy()
        df['20sma'] = df['close'].rolling(window=20).mean()
    
        # Ensure we have at least 25 candles to get a clean 20 SMA
        if len(df) < 25:
            return {'signal': False}
    
        # Step 10: Only allow trades between 9:30 and 13:30
        now = datetime.now().time()
        if not (time(9, 30) <= now <= time(13, 30)):
            return {'signal': False}
    
        # Last 4 candles needed for reference
        c3 = df.iloc[-3]
        c2 = df.iloc[-2]
        c1 = df.iloc[-1]
    
        # Step 2-3: C3 crosses above 20 SMA and closes above it
        cross_condition = (c3['close'] > c3['20sma']) and (c3['open'] < c3['20sma'])
    
        # Step 4: C2 closes above 20 SMA and does not touch it
        c2_above_sma = (c2['low'] > c2['20sma'])
    
        if not (cross_condition and c2_above_sma):
            return {'signal': False}
    
        # Step 5: IV filter
        if current_iv < 16:
            return {'signal': False}
    
        # Step 6: C1 crosses above max(c2.close, c3.high)
        breakout_level = max(c2['close'], c3['high'])
        if c1['close'] > breakout_level and c1['low'] < breakout_level:
            entry_price = c1['close']
            sl = round(entry_price * 0.90, 2)  # 10% SL
            target = round(entry_price * 1.05, 2)  # Initial 5% target
    
            return {
                'signal': True,
                'entry_price': entry_price,
                'sl': sl,
                'target': target,
                'reference_candle': c2.to_dict(),
                'entry_time': datetime.now()
            }
    
        return {'signal': False}
  

    
    
    # ─── DISPLAY ──────────────────────────────────────────────────────────────────
    #st.subheader("📊 Last 5 Candles")
    #st.dataframe(df.tail(5))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔹 Close", f"₹{latest['Close']:.2f}")
    col2.metric("🔸 EMA20", f"₹{latest['EMA20']:.2f}")
    #col3.metric("📌 Signal", signal)
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
