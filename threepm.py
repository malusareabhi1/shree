import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📊 NIFTY Last 100 Trading Days - Daily OLHCV Data")

# Fetch last 100 trading days of NIFTY (daily interval)
symbol = "^NSEI"  # Nifty 50 index
st.info("Fetching NIFTY 50 daily data...")

# Get data (100 trading days ≈ 140 calendar days)
data = yf.download(symbol, period="140d", interval="1d")

# Drop any incomplete rows
data.dropna(inplace=True)

# Keep only last 100 trading days
data = data.tail(100)

# Reset index to have Date as a column
data.reset_index(inplace=True)

# Rename and reorder columns for clarity
data = data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

# Display table
st.subheader("📋 NIFTY 100-Day OLHCV Table")
st.dataframe(data)

# Optional: CSV Download
csv = data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name='nifty_100_days_ohlcv.csv',
    mime='text/csv'
)
