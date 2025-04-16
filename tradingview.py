import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import yfinance as yf
from datetime import datetime, timedelta

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("📅 NIFTY50 Candlestick Viewer - Daily Chart")

nifty_50_stocks = {
    'Reliance': 'RELIANCE.NS', 'TCS': 'TCS.NS', 'Infosys': 'INFY.NS', 'HDFC Bank': 'HDFCBANK.NS',
    'ICICI Bank': 'ICICIBANK.NS', 'Axis Bank': 'AXISBANK.NS', 'Kotak Bank': 'KOTAKBANK.NS',
    'ITC': 'ITC.NS', 'LT': 'LT.NS', 'SBIN': 'SBIN.NS'
}

selected_stock = st.selectbox("📊 Select a NIFTY 50 Stock", options=list(nifty_50_stocks.keys()))

if selected_stock:
    symbol = nifty_50_stocks[selected_stock]
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)

    df = yf.download(symbol, start=start_date, end=end_date, interval='1d')
    df.dropna(inplace=True)

    st.subheader(f"📈 Daily Candlestick Chart for {selected_stock} ({symbol})")

    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Daily Candles'
    )])

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Price (INR)',
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Raw Data")
    st.dataframe(df.reset_index())
