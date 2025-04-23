import streamlit as st
import pandas as pd
import yfinance as yf

def fetch_data():
    data = yf.download('RELIANCE.NS', period='5d', interval='5m')
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
    return data

def main():
    st.title("🔍 Nifty Live Strategy")
    st.subheader("5-min EMA20 Strategy")

    data = fetch_data()

    # DEBUG: Show full column names and sample data
    st.write("✅ Data Columns:", data.columns.tolist())
    st.dataframe(data.tail())

    # Check if both columns exist
    if 'Close' in data.columns and 'EMA20' in data.columns:
        st.line_chart(data[['Close', 'EMA20']])
    else:
        st.error("❌ Columns 'Close' or 'EMA20' not found in data!")

if __name__ == "__main__":
    main()
