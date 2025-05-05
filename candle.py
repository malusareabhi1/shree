
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import time

# Function to fetch live 5-minute data for Nifty for 1 day
def fetch_5min_data(symbol):
    try:
        # Fetch data for today (1-day period) with 5-minute intervals
        df = yf.download(tickers=symbol, interval="5m", period="1d")
        df.dropna(inplace=True)  # Remove any missing data
        return df
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return None

# Function to plot the candlestick chart
def get_candlestick_chart(df, title="Nifty 5-Minute Candlestick Chart"):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close']
    )])
    fig.update_layout(
        title=title,
        xaxis_title='Time',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False
    )
    return fig

# Streamlit App
st.title("📊 Live Nifty 5-Minute Trend Candlestick Chart")

symbol = "^NSEI"  # Nifty 50 Index symbol in Yahoo Finance

# Display the live data and chart with a refresh every 30 seconds
while True:
    df = fetch_5min_data(symbol)  # Fetch data for Nifty
    st.write(df.head(10))
    if df is not None and not df.empty:
        st.plotly_chart(get_candlestick_chart(df, title="Live Nifty 5-Minute Candlestick Chart"), use_container_width=True)
    else:
        st.warning("No data available for the Nifty 5-Minute chart.")
    
    time.sleep(30)  # Refresh every 30 seconds
    #st.experimental_rerun()  # Re-run the app to fetch fresh data
