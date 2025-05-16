import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

# --- Streamlit UI ---
st.set_page_config(page_title="NSE Stock Data Viewer", layout="wide")
st.title("📈 NSE Stock Data Fetcher with Interval")

# Stock input
stock = st.text_input("Enter Stock Symbol (e.g., RELIANCE.NS, INFY.NS, GTLINFRA.NS)", value="RELIANCE.NS")

# Interval input
interval = st.selectbox("Select Interval", ['1m','2m','5m','15m','30m','60m','90m','1d','1wk','1mo'])

# Date range
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("2023-12-31"))

# Button
if st.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        try:
            df = yf.download(stock, interval=interval, start=start_date, end=end_date)

            if df.empty:
                st.warning("No data found for the selected parameters.")
            else:
                st.success(f"Data fetched for {stock} — {len(df)} rows")
                st.dataframe(df.tail(10))

                # Download CSV
                csv = df.to_csv().encode('utf-8')
                st.download_button("📥 Download CSV", csv, file_name=f"{stock}_{interval}.csv", mime='text/csv')

                # Candlestick Chart
                st.subheader("Candlestick Chart")
                fig = go.Figure(data=[go.Candlestick(x=df.index,
                                                     open=df['Open'],
                                                     high=df['High'],
                                                     low=df['Low'],
                                                     close=df['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=600)
                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")
