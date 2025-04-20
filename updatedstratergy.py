import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# Trade log to store trade details
trade_log = []

def fetch_data(stock_symbol, start_date, end_date, interval="5m"):
    try:
        data = yf.download(stock_symbol,
                           start=start_date,
                           end=end_date,
                           interval=interval,
                           progress=False)
        if data.empty:
            return pd.DataFrame()

        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data.dropna(inplace=True)
        return data

    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return pd.DataFrame()

def check_crossing(data):
    if 'Close' not in data.columns:
        raise KeyError("❌ 'Close' column is missing in the DataFrame!")

    # Calculate 20‑period SMA
    data['SMA_20'] = data['Close'].rolling(window=20).mean()

    # Drop rows where SMA is NaN (first 19 rows)
    data.dropna(subset=['SMA_20'], inplace=True)

    # Mark crossings
    data['crossed'] = (data['Close'] > data['SMA_20']).astype(int)
    return data

def check_iv(data, iv_threshold=16):
    # Mock IV — replace with real API call if available
    data['IV'] = 17
    data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
    return data

def execute_trade(data):
    for i in range(1, len(data)):
        if data['crossed'].iat[i] == 1 and data['iv_check'].iat[i] == 1:
            entry = data['Close'].iat[i]
            sl = entry * 0.90
            tg = entry * 1.05
            entry_time = data.index[i]
            
            # Log the trade details
            trade_log.append({
                'Entry Time': entry_time,
                'Entry Price': entry,
                'Stop Loss': sl,
                'Target Price': tg,
                'Status': 'Open'
            })
            
            st.success(f"✅ Trade @ ₹{entry:.2f}  SL: ₹{sl:.2f}  TG: ₹{tg:.2f}")
            return entry, sl, tg, entry_time
    st.info("ℹ️ No trade signal.")
    return None, None, None, None

def manage_risk(entry, sl, tg, data):
    for price in data['Close']:
        if price >= tg:
            st.success(f"🎯 Target hit @ ₹{price:.2f}")
            close_trade('Target Hit')
            return True
        if price <= sl:
            st.error(f"🛑 SL hit @ ₹{price:.2f}")
            close_trade('Stop Loss Hit')
            return True
    return False

def close_trade(status):
    # Update the last trade in the log to "Closed"
    if trade_log:
        trade_log[-1]['Status'] = status

# --- Streamlit UI ---
st.title("📊 Doctor Trade Strategy")

# Sidebar inputs
symbol = st.selectbox("Symbol", ["ADANIENT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBIN.NS",
    "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TCS.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"])
start = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=10))
end   = st.date_input("End Date",   datetime.date.today())
interval = st.selectbox("Interval", ["1m","5m","15m","30m","1h","3h","6h","12h","1d"])

if st.button("Fetch & Run"):
    df = fetch_data(symbol, start, end, interval)
    if df.empty:
        st.warning("⚠️ No data. Check symbol/date/interval (5m data only for last 60 days).")
    else:
        st.subheader("Raw Data")
        st.dataframe(df.tail(20))
        try:
            df = check_crossing(df)
            df = check_iv(df)

            # Plot
            fig = go.Figure([
                go.Candlestick(x=df.index,
                               open=df['Open'], high=df['High'],
                               low=df['Low'],   close=df['Close']),
                go.Scatter(     x=df.index,
                               y=df['SMA_20'],
                               mode='lines',
                               name='20 SMA')
            ])
            fig.update_layout(title=f"{symbol} ({interval})", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # Trade logic
            entry, sl, tg, t0 = execute_trade(df)
            if entry is not None:
                if manage_risk(entry, sl, tg, df):
                    st.info("🔁 Trade Closed (SL/TG hit)")

        except Exception as e:
            st.error(f"❌ Strategy error: {e}")

# Display trade log
if trade_log:
    st.subheader("Trade Log")
    trade_df = pd.DataFrame(trade_log)
    st.dataframe(trade_df)
