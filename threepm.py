import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📥 Download NIFTY 15-Minute Data (Last 60 Calendar Days)")

# Fetch NIFTY data
st.info("Fetching 15-minute NIFTY data... Yahoo Finance allows up to 60 calendar days for intraday data.")
data = yf.download("^NSEI", period="60d", interval="15m")

# Flatten columns if multi-indexed
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

# Drop missing
data.dropna(inplace=True)

# Reset index for CSV download
data.reset_index(inplace=True)

# Show preview
st.subheader("📊 NIFTY 15-Minute Data Preview")
st.dataframe(data.tail(10))

# Download as CSV
csv = data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV File",
    data=csv,
    file_name="nifty_15min_last_60days.csv",
    mime="text/csv"
)
