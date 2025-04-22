import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

st.title("📈 NIFTY 5-Minute Intraday Data Downloader")

# Input date
selected_date = st.date_input("Select a Date", value=date(2024, 4, 18))

# Download button
if st.button("Download NIFTY Data"):
    symbol = "^NSEI"
    start_date = selected_date.strftime("%Y-%m-%d")
    end_date = selected_date.strftime("%Y-%m-%d")

    with st.spinner("Downloading data..."):
        df = yf.download(tickers=symbol, interval="5m", start=start_date, end=end_date)

        if df.empty:
            st.error("⚠️ No data available. It might be a holiday or non-trading day.")
        else:
            # Filter for NSE trading hours
            df = df.between_time("09:15", "15:30")

            # Reset index to include datetime column for CSV
            df.reset_index(inplace=True)

            # Display data
            st.success("✅ Data fetched successfully!")
            st.dataframe(df)

            # Prepare download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"nifty_5min_{start_date}.csv",
                mime="text/csv"
            )
