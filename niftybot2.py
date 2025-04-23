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
        df = yf.download(tickers=symbol, interval=interval, period="1d")
        df.reset_index(inplace=True)
        df.rename(columns={"Datetime": "Datetime"}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching live data: {e}")
        return pd.DataFrame()

def load_csv_data(file=None):
    if file:
        return pd.read_csv(file)
    else:
        return pd.read_csv(DEFAULT_CSV_PATH)

# === Strategy Logic ===
def apply_strategy(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["Volume_Avg"] = df["Volume"].rolling(window=20).mean()
    df["Signal"] = ""

    for i in range(1, len(df)):
        if df["Close"][i] > df["EMA20"][i] and df["Volume"][i] > df["Volume_Avg"][i]:
            df.at[i, "Signal"] = "BUY"
        elif df["Close"][i] < df["EMA20"][i] and df["Volume"][i] > df["Volume_Avg"][i]:
            df.at[i, "Signal"] = "SELL"
    return df

# === Logger ===
def log_signals(df):
    logs = df[df["Signal"] != ""][["Datetime", "Close", "Signal"]]
    logs.to_csv(LOG_CSV, mode='a', index=False, header=not pd.io.common.file_exists(LOG_CSV))

# === Chart ===
def plot_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["Datetime"],
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candles"
    ))
    buy_signals = df[df["Signal"] == "BUY"]
    sell_signals = df[df["Signal"] == "SELL"]

    fig.add_trace(go.Scatter(
        x=buy_signals["Datetime"],
        y=buy_signals["Close"],
        mode="markers",
        marker=dict(symbol="triangle-up", color="green", size=10),
        name="BUY"
    ))
    fig.add_trace(go.Scatter(
        x=sell_signals["Datetime"],
        y=sell_signals["Close"],
        mode="markers",
        marker=dict(symbol="triangle-down", color="red", size=10),
        name="SELL"
    ))
    st.plotly_chart(fig, use_container_width=True)

# === Main Run ===
st.title("📊 Doctor Strategy Live Dashboard")
run_button = st.sidebar.button("Run Now")

if run_button or mode == "Live":
    while True:
        with st.spinner("Fetching data..."):
            if mode == "Live":
                df = get_live_data(symbol)
            else:
                df = load_csv_data(csv_file)

            if df.empty:
                st.warning("No data found.")
                break

            df = apply_strategy(df)
            st.subheader("Signal Table")
            st.dataframe(df[df["Signal"] != ""][["Datetime", "Close", "Signal"]], use_container_width=True)

            log_signals(df)
            st.subheader("Candlestick Chart")
            plot_chart(df)

            if mode == "CSV":
                break  # No loop for CSV mode
            else:
                time.sleep(interval)
                st.rerun()
