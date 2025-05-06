import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.set_page_config(layout="wide")
st.title("📊 Intraday Opening Range Breakout - NIFTY 50 Screener")

# List of NIFTY 50 symbols
nifty50_stocks = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE",
    "BAJAJFINSV", "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
    "ICICIBANK", "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NTPC",
    "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM",
    "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "UPL", "ULTRACEMCO", "WIPRO"
]
# Fetch 5-minute data
def fetch_5min_data(symbol):
    df = yf.download(tickers=symbol, interval="5m", period="1d", progress=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index = df.index.tz_convert("Asia/Kolkata")
    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["Open", "High", "Low", "Close"], inplace=True)
    return df

# Function to fetch and process data
def detect_orb(symbol):
    try:
        df = yf.download(tickers=symbol + ".NS", interval="5m", period="1d", progress=False)
        if df.empty:
            return None
        df.index = df.index.tz_convert("Asia/Kolkata")
        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
        
        opening_range = df.between_time("09:15", "09:30")
        if len(opening_range) < 3:
            return None
        
        or_high = opening_range["High"].max()
        or_low = opening_range["Low"].min()
        or_close_time = opening_range.index[-1]
        avg_volume = opening_range["Volume"].mean()
        
        post_or = df[df.index > or_close_time]

        for idx, row in post_or.iterrows():
            if row["Close"] > or_high and row["Volume"] > avg_volume:
                return {"Stock": symbol, "Signal": "🔼 Long", "Time": idx.time(), "Price": row["Close"]}
            elif row["Close"] < or_low and row["Volume"] > avg_volume:
                return {"Stock": symbol, "Signal": "🔽 Short", "Time": idx.time(), "Price": row["Close"]}
        return None
    except Exception:
        return None

# Progress and detection
# Create trade log table
trade_log = []

for stock in nifty50_stocks:
    symbol = stock + ".NS"
    df = fetch_5min_data(symbol)
    if df.empty:
        continue

    opening_range = df.between_time("09:15", "09:30")
    if len(opening_range) < 3:
        continue

    or_high = opening_range["High"].max()
    or_low = opening_range["Low"].min()
    or_close_time = opening_range.index[-1]
    post_or = df[df.index > or_close_time]

    for idx, row in post_or.iterrows():
        if row["Close"] > or_high and row["Volume"] > opening_range["Volume"].mean():
            trade_log.append({
                "Stock": stock,
                "Signal": "🔼 Long",
                "Time": idx.strftime("%H:%M"),
                "Price": row["Close"],
                "OR High": or_high,
                "OR Low": or_low
            })
            break
        elif row["Close"] < or_low and row["Volume"] > opening_range["Volume"].mean():
            trade_log.append({
                "Stock": stock,
                "Signal": "🔽 Short",
                "Time": idx.strftime("%H:%M"),
                "Price": row["Close"],
                "OR High": or_high,
                "OR Low": or_low
            })
            break

# Display table
st.subheader("📋 ORB Trade Log (Live Signals)")
if trade_log:
    st.dataframe(pd.DataFrame(trade_log))
else:
    st.info("No breakout signals found yet.")

