import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📥 Download NIFTY 15-Minute Data (Last 60 Days)")

# Step 1: Download data
data = yf.download("^NSEI", period="60d", interval="15m", progress=False)

# Step 2: Flatten MultiIndex if exists
if isinstance(data.columns, pd.MultiIndex):
    data.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in data.columns]

# Step 3: Drop missing
data.dropna(inplace=True)

# Step 4: Reset index and rename
data.reset_index(inplace=True)
data.columns = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'] if 'Adj Close' in data.columns else ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']

# Step 5: Display preview
st.subheader("📊 Preview of NIFTY 15-Minute Data")
st.dataframe(data.tail(10))

# Step 6: Download as CSV
csv = data.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV File",
    data=csv,
    file_name="nifty_15min_last_60days.csv",
    mime="text/csv"
)
