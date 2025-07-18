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
from datetime import datetime, timedelta,time
import os
import pytz
import ta  # Required for trend calculation (ensure installed)



# ─── SIDEBAR ─────────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Strategy Settings")

st.sidebar.title("📋 Navigation")
selected = st.sidebar.selectbox("Choose a section", [
    "Home",
    "Live Algo Trading",
    "Intraday Algo Trading",
    "Bollinger Band Breakout",
    "Intraday Paper Trading",
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
    st.title("📊 Nifty 5-min EMA20 + Volume Breakout Monitor")
    
    # ─── STRATEGY TEST STARTED ─────────────────────────────────────────────────────
    start_msg = "🟢 Strategy Test Started"
    st.info(start_msg)
    send_telegram(start_msg)
    
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
    signal = "No Signal"
    if (prev["Close"] < prev["EMA20"]) and (latest["Close"] > prev["EMA20"]) and (latest["Volume"] > latest["VMA20"]):
        signal = "BUY"
        entry_price = round(latest["Close"], 2)
        msg = (
            f"📥 <b>LIVE BUY SIGNAL</b>\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Entry:</b> ₹{entry_price}\n"
            f"<b>Volume:</b> {latest['Volume']:,}\n"
            f"<b>Time:</b> {latest.name.strftime('%H:%M')}"
        )
        send_telegram(msg)

    
    
    # ─── DISPLAY ──────────────────────────────────────────────────────────────────
    st.subheader("📊 Last 5 Candles")
    st.dataframe(df.tail(5))
    
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
    st.subheader("📈 Price vs EMA20")
    st.line_chart(df[["Close", "EMA20"]])
    
    # ─── STRATEGY TEST STOPPED ────────────────────────────────────────────────────
    stop_msg = "🔴 Strategy Test Ended (for current run)"
    st.info(stop_msg)
    send_telegram(stop_msg)
    
    # ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
    st.markdown("⏱️ Auto-refresh every 30 seconds")
    with st.spinner("⏳ Refreshing in 30 seconds..."):
        time.sleep(30)
        st.rerun()

elif selected == "Intraday Algo Trading":
    st.header("📊 Intraday ORB Strategy (Opening Range Breakout)")
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup
    from nsetools import Nse
    uploaded_file = st.file_uploader("Upload CSV file with OHLCV data", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        #______________________________________________________________________
        # Convert the datetime column (assume it's named 'Datetime') to datetime object
        #df['Date'] = pd.to_datetime(df['Date'])
        #st.write(df.columns.tolist())
        # Localize to UTC if it's naive (no timezone info), then convert to Asia/Kolkata
        #if df['Date'].dt.tz is None:
           # df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        #else:
            #df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')
        
        # Set as index (optional but useful for time-based slicing)
        #df.set_index('Date', inplace=True)


        #_________________________________________________________________________
        #        st.subheader("Available Columns in Uploaded File:")
        #        st.write(df.columns.tolist())

        # Let user select the datetime column
        
        datetime_col = st.selectbox("Select your Datetime column", df.columns)

        try:
            df[datetime_col] = pd.to_datetime(df[datetime_col])
            df['Time'] = df[datetime_col].dt.time
            df['Date'] = df[datetime_col].dt.date
            st.success("Datetime parsed successfully.")
            st.dataframe(df.head(50))
        except Exception as e:
            st.error(f"❌ Failed to parse datetime: {e}")
    else:
        st.warning("📂 Please upload a CSV file to begin.")
        

    # Filter today's date and opening range (9:15 to 9:30)
    today = df['Date'].iloc[-1]
    today_df = df[df['Date'] == today]

    #opening_range = today_df[(today_df['Time'] >= datetime.time(9,15)) & (today_df['Time'] <= datetime.time(9,30))]
    opening_range = today_df[(today_df['Time'] >= time(9,15)) & (today_df['Time'] <= time(9,30))]
    or_high = opening_range['High'].max()
    or_low = opening_range['Low'].min()

    st.write(f"🔼 Opening Range High: {or_high}")
    st.write(f"🔽 Opening Range Low: {or_low}")
    #st.write("Available columns:", today_df.columns.tolist())

    # Find breakout
    trade_signal = None
    #breakout_df = today_df[today_df['Time'] > datetime.time(9,30)]
    breakout_df = today_df[today_df['Time'] > time(9, 30)]


    for i, row in breakout_df.iterrows():
        if row['High'] > or_high and trade_signal is None:
            trade_signal = "BUY"
            entry_price = row['Close']
            stop_loss = or_low
            target = entry_price + (entry_price - stop_loss) * 1.5
            entry_time = row['Time']
            break
        elif row['Low'] < or_low and trade_signal is None:
            trade_signal = "SELL"
            entry_price = row['Close']
            stop_loss = or_high
            target = entry_price - (stop_loss - entry_price) * 1.5
            entry_time = row['Time']
            break

    if trade_signal:
        st.success(f"📌 Signal: {trade_signal}")
        st.write(f"📍 Entry Price: {entry_price}")
        st.write(f"⛔ Stop Loss: {stop_loss}")
        st.write(f"🎯 Target: {target}")
        st.write(f"⏰ Time: {entry_time}")
    else:
        st.warning("No breakout signal found today.")

#_________________________________________________________________________________________________________________
elif selected == "Intraday Paper Trading":
    st.header("📊 Intraday ORB Strategy (Opening Range Breakout)")

    # 1. Read the uploaded CSV
    uploaded_file = st.file_uploader("Upload CSV file with OHLCV data", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # 2. Select datetime column
        datetime_col = st.selectbox("Select your Datetime column", df.columns)

        # 3. Convert selected column to datetime
        df[datetime_col] = pd.to_datetime(df[datetime_col])

        # 4. Make a new 'Date' column from datetime_col
        df['Date'] = df[datetime_col]

        # 5. Check timezone
        if df['Date'].dt.tz is None:
            df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        else:
            df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')

        # 6. Set 'Date' as index
        df.set_index('Date', inplace=True)

        # 7. Show dataframe (optional)
        st.write("Uploaded Data:", df.head())

        # 8. ➡️ PAPER TRADING CODE STARTS HERE

        capital = 100000  # Total capital
        risk_per_trade = 0.02  # 2% risk per trade
        position_size = capital * risk_per_trade

        trades = []
        in_position = False
        entry_price = None
        entry_time = None

        for i in range(1, len(df)):
            row_prev = df.iloc[i - 1]
            row = df.iloc[i]

            if not in_position and row_prev['Close'] > row_prev['Open']:
                entry_price = row['Open']
                entry_time = row.name
                in_position = True
                trades.append({
                    'Type': 'BUY',
                    'Entry Time': entry_time,
                    'Entry Price': entry_price
                })

            elif in_position and row_prev['Close'] < row_prev['Open']:
                exit_price = row['Open']
                exit_time = row.name
                pnl = (exit_price - entry_price) * (position_size / entry_price)
                trades[-1].update({
                    'Exit Time': exit_time,
                    'Exit Price': exit_price,
                    'PnL': round(pnl, 2)
                })
                in_position = False

        

        # After trading simulation
        trades_df = pd.DataFrame(trades)

        # Performance metrics
        total_trades = len(trades_df)
        gross_pnl = trades_df['PnL'].sum()

        turnover = 0
        if not trades_df.empty:
            turnover = (trades_df['Entry Price'].sum() + trades_df['Exit Price'].sum()) * (position_size / trades_df['Entry Price'].mean())

        tax_rate = 0.0003  # 0.03% brokerage + other taxes approx
        taxes = turnover * tax_rate
        net_pnl = gross_pnl - taxes
        # Success ratio calculation
        winning_trades = trades_df[trades_df['PnL'] > 0]
        success_ratio = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0

        # Display performance
        st.subheader("📈 Performance Report:")
        st.write(f"**Total Capital:** ₹{capital:,.2f}")
        st.write(f"**Total Trades:** {total_trades}")
        st.write(f"**Total Turnover:** ₹{turnover:,.2f}")
        st.write(f"**Total Taxes (approx):** ₹{taxes:,.2f}")
        st.write(f"**Gross P&L:** ₹{gross_pnl:,.2f}")
        st.success(f"**Net P&L after Taxes:** ₹{net_pnl:,.2f}")
        st.write(f"**Success Ratio:** {success_ratio:.2f}% ✅")

        # Show trades table
        st.subheader("📋 Trade Log:")
        st.dataframe(trades_df)

        # Download CSV button
        csv = trades_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Trades CSV",
            data=csv,
            file_name='paper_trades.csv',
            mime='text/csv',
        )

#_________________________________________________________________________________________________________________
elif selected == "Bollinger Band Breakout":
    #import pandas_ta as ta
    #Bollinger Band Breakout
    # File Upload
    import pandas_ta as ta
    st.title("Algo Trading BOT - Bollinger Band Breakout")

    uploaded_file = st.file_uploader("Upload CSV File", type=['csv'])
    
    if uploaded_file is not None:
        # Read CSV
        #df = pd.read_csv(uploaded_file)
    
        df = pd.read_csv(uploaded_file)

        # 2. Select datetime column
        datetime_col = st.selectbox("Select your Datetime column", df.columns)

        # 3. Convert selected column to datetime
        df[datetime_col] = pd.to_datetime(df[datetime_col])

        # 4. Make a new 'Date' column from datetime_col
        df['Date'] = df[datetime_col]

        # 5. Check timezone
        if df['Date'].dt.tz is None:
            df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        else:
            df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')

        # 6. Set 'Date' as index
        df.set_index('Date', inplace=True)

        # 7. Show dataframe (optional)
        st.write("Uploaded Data:", df.head())
    
        st.success("CSV File Loaded Successfully!")
    
        selected = st.selectbox("Select Strategy", ["Bollinger Band Breakout"])
    
        if selected == "Bollinger Band Breakout":
            st.subheader("Running Bollinger Band Breakout Strategy... 🚀")
    
            # Parameters
            period = 20  # Bollinger Band period
            stddev = 2   # Standard deviation multiplier
    
            # Calculate Bollinger Bands
            #df['UpperBand'], df['MiddleBand'], df['LowerBand'] = talib.BBANDS(df['Close'], timeperiod=period, nbdevup=stddev, nbdevdn=stddev, matype=0)
            # Calculate Bollinger Bands with pandas-ta
            df['UpperBand'], df['MiddleBand'], df['LowerBand'] = ta.bbands(df['Close'], length=period, std=stddev)

    
            # Create Signal Column
            df['Signal'] = None
    
            # Simple breakout logic
            for i in range(1, len(df)):
                if df['Close'][i] > df['UpperBand'][i] and df['Close'][i-1] <= df['UpperBand'][i-1]:
                    df.at[i, 'Signal'] = 'BUY'
                elif df['Close'][i] < df['LowerBand'][i] and df['Close'][i-1] >= df['LowerBand'][i-1]:
                    df.at[i, 'Signal'] = 'SELL'
    
            # Show Result
            st.dataframe(df[['Datetime', 'Close', 'UpperBand', 'MiddleBand', 'LowerBand', 'Signal']].tail(50))
    
            # Plotting
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df['Datetime'], df['Close'], label='Close Price', color='black')
            ax.plot(df['Datetime'], df['UpperBand'], label='Upper Band', linestyle='--', color='green')
            ax.plot(df['Datetime'], df['MiddleBand'], label='Middle Band', linestyle='--', color='blue')
            ax.plot(df['Datetime'], df['LowerBand'], label='Lower Band', linestyle='--', color='red')
    
            # Plot BUY/SELL signals
            buy_signals = df[df['Signal'] == 'BUY']
            sell_signals = df[df['Signal'] == 'SELL']
            ax.scatter(buy_signals['Datetime'], buy_signals['Close'], marker='^', color='green', label='Buy Signal', s=100)
            ax.scatter(sell_signals['Datetime'], sell_signals['Close'], marker='v', color='red', label='Sell Signal', s=100)
    
            ax.set_title('Bollinger Band Breakout Strategy')
            ax.legend()
            ax.grid()
    
            st.pyplot(fig)
    
    else:
        st.warning("Please upload a CSV file to continue.")
    
