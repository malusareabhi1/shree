import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.title("📊 NIFTY 50 Stock Viewer")

# List of some popular NIFTY 50 stock symbols (Yahoo Finance tickers)
nifty50_stocks = {
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "State Bank of India": "SBIN.NS",
    "Axis Bank": "AXISBANK.NS",
    "Larsen & Toubro": "LT.NS"
}

# Dropdown to select stock
stock_name = st.selectbox("Select a NIFTY 50 Stock", list(nifty50_stocks.keys()))
ticker = nifty50_stocks[stock_name]

# Date range: last 30 days
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

# Fetch data
data = yf.download(ticker, start=start_date, end=end_date)

# Display
st.subheader(f"📈 Last 30 Days Data for {stock_name} ({ticker})")
st.dataframe(data)

# Optional: Plot the closing price
st.line_chart(data['Close'])
