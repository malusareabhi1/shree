import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
from datetime import datetime
import yfinance as yf
import requests

st.set_page_config(layout="wide")

# === CONFIG ===
REFRESH_INTERVAL = 30  # seconds
LOG_CSV = "trade_logs.csv"
DEFAULT_CSV_PATH = "stock_data.csv"

# === SIDEBAR ===
st.sidebar.title("📈 Strategy Dashboard")
mode = st.sidebar.radio("Select Mode", ["Live", "CSV"])
interval = st.sidebar.number_input("Refresh Interval (sec)", value=REFRESH_INTERVAL, min_value=5, step=5)
csv_file = st.sidebar.file_uploader("Upload CSV", type="csv")
symbol = st.sidebar.text_input("Stock Symbol", value="RELIANCE.BO")

# === Load Data ===
def get_live_data(symbol="RELIANCE.BO", interval="5m"):
    try:
        df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.reset_index().rename(columns={"Datetime": "datetime"})
        return df
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        return pd.DataFrame()


def load_csv_data(file=None):
    try:
        if file:
            df = pd.read_csv(file)
        else:
            df = pd.read_csv(DEFAULT_CSV_PATH)
        return df
    except Exception as e:
        st.error(f"Error loading CSV data: {e}")
        return pd.DataFrame()

# === Strategy Logic ===
def apply_strategy(df):
    if df is None or df.empty:
        st.warning("DataFrame is empty. Skipping strategy.")
        return pd.DataFrame()

    # Normalize column names
    df.columns = [col.strip().lower() for col in df.columns]

    required_cols = {"close", "volume", "open", "high", "low", "datetime"}
    missing = required_cols - set(df.columns)
    if missing:
        st.error(f"Missing required columns: {missing}")
        return pd.DataFrame()

    # Ensure datetime column is in datetime format
    df["datetime"] = pd.to_datetime(df["datetime"])

    # Indicators
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["volume_avg"] = df["volume"].rolling(window=20).mean()
    df["signal"] = ""

    for i in range(1, len(df)):
        if df["close"].iat[i] > df["ema20"].iat[i] and df["volume"].iat[i] > df["volume_avg"].iat[i]:
            df.at[i, "signal"] = "BUY"
        elif df["close"].iat[i] < df["ema20"].iat[i] and df["volume"].iat[i] > df["volume_avg"].iat[i]:
            df.at[i, "signal"] = "SELL"
    return df

# === Logger ===
def log_signals(df):
    if df is None or df.empty:
        return
    logs = df[df["signal"] != ""][['datetime', 'close', 'signal']]
    header = not os.path.exists(LOG_CSV)
    logs.to_csv(LOG_CSV, mode='a', index=False, header=header)

# === Chart ===
def plot_chart(df):
    if df is None or df.empty:
        return
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["datetime"], open=df["open"], high=df["high"], low=df["low"], close=df["close"], name="Candles"
    ))
    buy_signals = df[df["signal"] == "BUY"]
    sell_signals = df[df["signal"] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buy_signals["datetime"], y=buy_signals["close"], mode="markers",
        marker=dict(symbol="triangle-up", color="green", size=10), name="BUY"
    ))
    fig.add_trace(go.Scatter(
        x=sell_signals["datetime"], y=sell_signals["close"], mode="markers",
        marker=dict(symbol="triangle-down", color="red", size=10), name="SELL"
    ))
    st.plotly_chart(fig, use_container_width=True)

# === Main Run ===
st.title("📊 Doctor Strategy Live Dashboard")
run = st.sidebar.button("Run Now")

if run or mode == "Live":
    while True:
        with st.spinner("Fetching data..."):
            if mode == "Live":
                df = get_live_data(symbol, "5m")
            else:
                df = load_csv_data(csv_file)

            st.write("DataFrame info:", type(df), df.shape)
            df = apply_strategy(df)

            st.subheader("Signal Table")
            if not df.empty:
                st.dataframe(df[df['signal'] != ''][['datetime', 'close', 'signal']], use_container_width=True)
                log_signals(df)
                st.subheader("Candlestick Chart")
                plot_chart(df)
            else:
                st.warning("No data/signals to display.")

            if mode == "CSV":
                break  # No loop for CSV mode
            else:
                time.sleep(interval)
                st.rerun()
