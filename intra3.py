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
orb_results = []
progress = st.progress(0)
for i, stock in enumerate(nifty50_stocks):
    result = detect_orb(stock)
    if result:
        orb_results.append(result)
    progress.progress((i + 1) / len(nifty50_stocks))

# Display Results
if orb_results:
    st.success("ORB Signals Found ✅")
    result_df = pd.DataFrame(orb_results)
    st.dataframe(result_df)
else:
    st.warning("No ORB signals detected in NIFTY 50 today.")
