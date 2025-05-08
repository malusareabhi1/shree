import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import os
import pytz
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Doctor Strategy Dashboard", layout="wide")
st.title("🩺 Doctor Strategy Live Signal Dashboard")

# Configuration
symbol = "^NSEI"  # NIFTY 50 index symbol for Yahoo Finance
interval = "5m"
lookback_minutes = 1000
iv_threshold = 16  # Placeholder; replace with live IV
log_file = "doctor_signal_log.csv"

# Load previous log if exists
if os.path.exists(log_file):
    signal_log = pd.read_csv(log_file)
else:
    signal_log = pd.DataFrame(columns=[
        "Date", "Close", "SMA_20", "Upper_BB", "Lower_BB",
        "Signal", "Entry_Price", "IV"
    ])

# Fetch data function
def get_nifty_data():
    df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("Asia/Kolkata")
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Date"}, inplace=True)
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    return df

# Doctor Strategy logic
def doctor_strategy_signals(df, iv_threshold=16, capital=50000):
    df['Date'] = pd.to_datetime(df['Date'])
    if df['Date'].dt.tz is None:
        df['Date'] = df['Date'].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    else:
        df['Date'] = df['Date'].dt.tz_convert("Asia/Kolkata")

    df = df[df['Date'].dt.time.between(pd.to_datetime('09:30:00').time(), pd.to_datetime('13:30:00').time())]
    df = df.sort_values('Date').reset_index(drop=True)

    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
    df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()

    df['Crossed_SMA_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) < df['SMA_20'].shift(1))
    df['Ref_Candle_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) > df['SMA_20'].shift(1))

    df['Signal'] = None
    for i in range(1, len(df)):
        if df['Ref_Candle_Up'].iloc[i] and iv_threshold >= 16:
            if df['Close'].iloc[i] > df['Close'].iloc[i - 1]:
                df.at[i, 'Signal'] = 'BUY'

    trades = []
    for i in range(len(df)):
        if df['Signal'].iloc[i] == 'BUY':
            entry_time = df['Date'].iloc[i]
            entry_price = df['Close'].iloc[i]
            stop_loss = entry_price * 0.90
            profit_target = entry_price * 1.05
            exit_time = None
            exit_price = None
            exit_reason = None
            pnl = None

            for j in range(i + 1, min(i + 12, len(df))):
                price = df['Close'].iloc[j]
                if price >= profit_target:
                    exit_time = df['Date'].iloc[j]
                    exit_price = profit_target
                    exit_reason = "Target Hit"
                    break
                elif price <= stop_loss:
                    exit_time = df['Date'].iloc[j]
                    exit_price = stop_loss
                    exit_reason = "Stop Loss Hit"
                    break
            else:
                if i + 10 < len(df):
                    exit_time = df['Date'].iloc[i + 10]
                    exit_price = df['Close'].iloc[i + 10]
                    exit_reason = "Time Exit"

            if exit_price:
                turnover = entry_price + exit_price
                pnl = (exit_price - entry_price) * (capital // entry_price) - 20  # ₹20 brokerage
                trades.append({
                    "Entry_Time": entry_time,
                    "Entry_Price": entry_price,
                    "Exit_Time": exit_time,
                    "Exit_Price": exit_price,
                    "Stop_Loss": stop_loss,
                    "Profit_Target": profit_target,
                    "Exit_Reason": exit_reason,
                    "Brokerage": 20,
                    "PnL": round(pnl, 2),
                    "Turnover": round(turnover, 2)
                })

    return df, trades

# Plot candles with SMA
def plot_candles_with_sma(df):
    df['20-SMA'] = df['Close'].rolling(window=20).mean()
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
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

# Main logic
df = get_nifty_data()
df.rename(columns={df.columns[0]: "Date"}, inplace=True)
df.reset_index(drop=True, inplace=True)

if df.empty:
    st.warning("No data available for today’s 5‑min bars.")
else:
    st.subheader("📊 Candlestick Chart")
    st.plotly_chart(plot_candles_with_sma(df), use_container_width=True)

    df_result, trade_log = doctor_strategy_signals(df)
    st.subheader("🧪 Ref Candle Up Log")
    st.dataframe(df_result[['Date', 'Close', 'SMA_20', 'Ref_Candle_Up']].tail(50), use_container_width=True)


    st.subheader("📈 Signals")
    st.dataframe(df_result[['Date', 'Close', 'SMA_20', 'Signal']].dropna(subset=['Signal']), use_container_width=True)

    st.subheader("📘 Trade Log")
    st.dataframe(pd.DataFrame(trade_log), use_container_width=True)

    # Optional: Auto-refresh every 30 seconds
    st_autorefresh(interval=30000, key="refresh")
