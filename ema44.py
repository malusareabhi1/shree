import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📈 44-MA Strategy Tester (Live & CSV)")

# Sidebar input
data_source = st.sidebar.radio("Select Data Source", ["Live (yFinance)", "CSV Upload"])

# Function to calculate 44 MA strategy
def apply_strategy(df):
    df["MA44"] = df["Close"].rolling(window=44).mean()
    df["Buy"] = (df["Close"] > df["MA44"]) & (df["Close"].shift(1) <= df["MA44"].shift(1))
    df["Sell"] = (df["Close"] < df["MA44"]) & (df["Close"].shift(1) >= df["MA44"].shift(1))
    return df

# Load live data
if data_source == "Live (yFinance)":
    ticker = st.sidebar.text_input("Enter Stock Symbol (e.g., TCS.NS, INFY.BO)", "TCS.NS")
    period = st.sidebar.selectbox("Data Period", ["3mo", "6mo", "1y", "2y", "5y"])
    interval = st.sidebar.selectbox("Interval", ["1d", "1h", "5m"])
    
    if st.sidebar.button("Fetch Live Data"):
        df = yf.download(ticker, period=period, interval=interval)
        df = df.reset_index()
        st.success(f"Fetched {ticker} data successfully!")
        df = apply_strategy(df)

# Load CSV data
elif data_source == "CSV Upload":
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = [col.strip().capitalize() for col in df.columns]
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            df = df.reset_index(drop=True)
        df = apply_strategy(df)

# Display chart and signals
if 'df' in locals():
    st.subheader("📊 Price Chart with 44 MA")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df['Date'], df['Close'], label='Close Price', color='black')
    ax.plot(df['Date'], df['MA44'], label='44 MA', color='orange')

    buy_signals = df[df['Buy']]
    sell_signals = df[df['Sell']]
    ax.plot(buy_signals['Date'], buy_signals['Close'], '^', markersize=10, color='green', label='Buy Signal')
    ax.plot(sell_signals['Date'], sell_signals['Close'], 'v', markersize=10, color='red', label='Sell Signal')

    ax.set_title("44 MA Strategy Backtest")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("📋 Signal Table")
    signals = df[df['Buy'] | df['Sell']][['Date', 'Close', 'Buy', 'Sell']]
    st.dataframe(signals.reset_index(drop=True))

    st.subheader("📈 Strategy Summary")
    total_signals = len(signals)
    buy_count = df['Buy'].sum()
    sell_count = df['Sell'].sum()
    st.markdown(f"""
    - ✅ Total Signals: **{total_signals}**
    - 🟢 Buy Signals: **{buy_count}**
    - 🔴 Sell Signals: **{sell_count}**
    """)
