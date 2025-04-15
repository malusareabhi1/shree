# intraday_scanner.py (Streamlit Demo)

import random
from datetime import datetime
import streamlit as st
import pandas as pd

# --- Mock NIFTY 50 stock data for simulation ---
nifty50_stocks = [
    "ADANIENT", "ADANIPORTS", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV",
    "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT",
    "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NTPC", "NESTLEIND",
    "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS",
    "TATASTEEL", "TECHM", "TITAN", "UPL", "ULTRACEMCO", "WIPRO"
]

# --- Generate mock stock data ---
def generate_mock_data():
    mock_data = []
    for symbol in nifty50_stocks:
        open_price = random.uniform(100, 1500)
        price = open_price * random.uniform(0.98, 1.05)
        prev_close = open_price * random.uniform(0.97, 1.03)
        volume = random.randint(400000, 1200000)
        mock_data.append({
            "symbol": symbol,
            "price": round(price, 2),
            "volume": volume,
            "open_price": round(open_price, 2),
            "prev_close": round(prev_close, 2)
        })
    return mock_data

# --- Scanner configuration ---
MIN_VOLUME = 500000
PRICE_RANGE = (50, 1500)
PRICE_CHANGE_THRESHOLD = 0.015  # 1.5%

# --- Simulate technical conditions ---
def simulate_technical_conditions(stock):
    rsi = random.randint(25, 75)
    vwap = stock['open_price'] + random.uniform(-10, 10)
    above_vwap = stock['price'] > vwap
    breakout_15min = stock['price'] > stock['open_price'] * 1.015
    return rsi, above_vwap, breakout_15min

# --- Scan logic ---
def scan_intraday_stocks(stocks):
    shortlisted = []
    for stock in stocks:
        if PRICE_RANGE[0] <= stock['price'] <= PRICE_RANGE[1] and stock['volume'] >= MIN_VOLUME:
            price_change = (stock['price'] - stock['prev_close']) / stock['prev_close']
            if abs(price_change) >= PRICE_CHANGE_THRESHOLD:
                rsi, above_vwap, breakout_15min = simulate_technical_conditions(stock)

                if above_vwap and breakout_15min:
                    shortlisted.append({
                        "symbol": stock['symbol'],
                        "price": stock['price'],
                        "rsi": rsi,
                        "above_vwap": above_vwap,
                        "breakout": breakout_15min,
                        "volume": stock['volume']
                    })
    return shortlisted

# --- Streamlit UI ---
st.set_page_config(page_title="Intraday Stock Finder", layout="wide")
st.title("📈 Intraday Stock Finder (NSE)")

mock_stocks = generate_mock_data()
result = scan_intraday_stocks(mock_stocks)

if result:
    df = pd.DataFrame(result)
    st.success(f"{len(df)} stocks shortlisted for intraday trading")
    st.dataframe(df)
else:
    st.warning("No suitable intraday stocks found based on current filters.")
