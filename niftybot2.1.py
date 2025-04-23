import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime
import yfinance as yf

st.set_page_config(layout="wide")

# === CONFIG ===
REFRESH_INTERVAL = 30  # seconds
LOG_CSV = "trade_logs.csv"

# === SIDEBAR ===
st.sidebar.title("📈 Live Strategy Dashboard")
interval = st.sidebar.number_input("Refresh Interval (sec)", value=REFRESH_INTERVAL, min_value=5, step=5)
symbol = st.sidebar.text_input("Stock Symbol", value="^NSEI")

# === Load Live Data ===
def get_live_data(symbol: str, interval_str: str = "5m") -> pd.DataFrame:
    try:
        df = yf.download(tickers=symbol, interval=interval_str, period="1d", progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        # Reset index to turn the DatetimeIndex into a column
        df = df.reset_index()
        # Rename the first column (whatever its name) to 'datetime'
        datetime_col = df.columns[0]
        df.rename(columns={datetime_col: 'datetime'}, inplace=True)
        df.csv('data.csv');
        return df
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        return pd.DataFrame()

# === Strategy Logic ===
def apply_strategy(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    # Normalize all column names to lowercase
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Ensure 'datetime' exists
    if 'datetime' not in df.columns:
        st.error("Column 'datetime' not found after rename.")
        return pd.DataFrame()

    # Required columns
    required_cols = {'datetime', 'open', 'high', 'low', 'close', 'volume'}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {missing}")
        return pd.DataFrame()

    # Parse datetime column
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Calculate indicators
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['volume_avg'] = df['volume'].rolling(window=20).mean()
    df['signal'] = ''

    # Generate signals
    for i in range(1, len(df)):
        if df['close'].iat[i] > df['ema20'].iat[i] and df['volume'].iat[i] > df['volume_avg'].iat[i]:
            df.at[i, 'signal'] = 'BUY'
        elif df['close'].iat[i] < df['ema20'].iat[i] and df['volume'].iat[i] > df['volume_avg'].iat[i]:
            df.at[i, 'signal'] = 'SELL'
    return df

# === Logger ===
def log_signals(df: pd.DataFrame):
    if df is None or df.empty:
        return
    logs = df[df['signal'] != ''][['datetime', 'close', 'signal']]
    if logs.empty:
        return
    header_flag = not os.path.exists(LOG_CSV)
    logs.to_csv(LOG_CSV, mode='a', index=False, header=header_flag)

# === Chart ===
def plot_chart(df: pd.DataFrame):
    if df is None or df.empty:
        return
    fig = go.Figure()
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['datetime'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Candles'
    ))
    # EMA line
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['ema20'], mode='lines', name='EMA20', line=dict(color='blue')
    ))
    # Signal markers
    buys = df[df['signal'] == 'BUY']
    sells = df[df['signal'] == 'SELL']
    fig.add_trace(go.Scatter(
        x=buys['datetime'], y=buys['close'], mode='markers', marker=dict(symbol='triangle-up', color='green', size=10), name='BUY'
    ))
    fig.add_trace(go.Scatter(
        x=sells['datetime'], y=sells['close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=10), name='SELL'
    ))
    fig.update_layout(xaxis_rangeslider_visible=False, template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

# === Main Loop ===
st.title("📊 Doctor Strategy Live Dashboard")

while True:
    with st.spinner("Fetching live data..."):
        df_live = get_live_data(symbol, "5m")
        st.write(f"DataFrame shape: {df_live.shape}")
        df_signals = apply_strategy(df_live)

        if not df_signals.empty:
            st.subheader("Live Signals")
            st.dataframe(df_signals[df_signals['signal'] != ''][['datetime', 'close', 'signal']], use_container_width=True)
            log_signals(df_signals)
            st.subheader("Live Candlestick Chart with EMA20")
            plot_chart(df_signals)
        else:
            st.warning("No data or signals available currently.")

    time.sleep(interval)
    st.experimental_rerun()
