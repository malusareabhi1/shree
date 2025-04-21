import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# Function to fetch today's data (5-minute interval)
def fetch_today_data(stock_symbol):
    stock_data = yf.download(stock_symbol, period="1d", interval="5m")
    return stock_data

# Function to plot candlestick chart
def plot_candlestick_chart(df, stock_symbol):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=stock_symbol
    )])

    fig.update_layout(
        title=f"{stock_symbol} - Today's Candlestick Chart",
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig)

# Streamlit UI
st.title("📈 Live Candlestick Chart")

stock_symbol = st.text_input("Enter Stock Symbol (e.g., NIFTY, AAPL, TSLA):", "NIFTY")

if stock_symbol:
    st.write(f"Fetching data for {stock_symbol}...")
    df = fetch_today_data(stock_symbol)

    st.subheader("📝 Today's Data")
    st.write(df.tail())

    plot_candlestick_chart(df, stock_symbol)
