import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Function to fetch stock data
def fetch_data(stock, start, end):
    data = yf.download(stock, start=start, end=end)
    return data

# Function to calculate the 14-day RSI
def calculate_rsi(data, period=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

# Function to calculate the moving averages (SMA)
def calculate_sma(data, period):
    return data['Close'].rolling(window=period).mean()

# Function to calculate Bollinger Bands
def calculate_bollinger_bands(data, period=20):
    rolling_mean = data['Close'].rolling(window=period).mean()
    rolling_std = data['Close'].rolling(window=period).std()
    
    upper_band = rolling_mean + (rolling_std * 2)
    lower_band = rolling_mean - (rolling_std * 2)
    
    return upper_band, rolling_mean, lower_band

# Function to generate action plan based on technical setup
def generate_action_plan(data):
    latest_close = data['Close'].iloc[-1]
    sma50 = data['SMA50'].iloc[-1]
    sma200 = data['SMA200'].iloc[-1]
    rsi = data['RSI'].iloc[-1]
    upper_band = data['Upper_Band'].iloc[-1]
    lower_band = data['Lower_Band'].iloc[-1]

    action = "No action suggested."

    if latest_close > sma50 and latest_close > sma200:
        action = "Bullish: Consider buying or holding."
    elif latest_close < sma50 and latest_close < sma200:
        action = "Bearish: Consider selling or shorting."
    elif latest_close > upper_band:
        action = "Overbought: Be cautious, consider selling."
    elif latest_close < lower_band:
        action = "Oversold: Consider buying."
    elif rsi > 70:
        action = "Overbought: Consider selling."
    elif rsi < 30:
        action = "Oversold: Consider buying."

    summary = f"RSI: {rsi:.2f}, Close: {latest_close}, 50-Day SMA: {sma50:.2f}, 200-Day SMA: {sma200:.2f}, Bollinger Bands: Upper - {upper_band:.2f}, Lower - {lower_band:.2f}"

    return action, summary

# Streamlit layout
st.title("📊 Stock Analysis Tool")
st.write("Looking at your STOCK name, here’s a quick analysis and possible action plan based on the indicators and price action.")

# User input for stock and date range
stock = st.text_input("Enter Stock Symbol (e.g., AAPL, TSLA, RELIANCE)", "AAPL")
start_date = st.date_input("Start Date", pd.to_datetime('2022-01-01'))
end_date = st.date_input("End Date", pd.to_datetime('2023-01-01'))

# Fetch data and calculate indicators
if stock:
    data = fetch_data(stock, start_date, end_date)
    if not data.empty:
        # Calculate indicators
        data['RSI'] = calculate_rsi(data)
        data['SMA50'] = calculate_sma(data, 50)
        data['SMA200'] = calculate_sma(data, 200)
        data['Upper_Band'], data['Middle_Band'], data['Lower_Band'] = calculate_bollinger_bands(data)

        # Display the data and indicators
        st.subheader(f"Stock Data for {stock.upper()}")
        st.write(data.tail())

        # Generate action plan
        action, summary = generate_action_plan(data)

        # Display results
        st.subheader("📈 Analysis Summary")
        st.write(f"**Possible Actions:** {action}")
        st.write(f"**Technical Setup Observed:**")
        st.write(summary)

        # Plot stock data
        st.subheader("📉 Stock Price and Indicators")
        st.line_chart(data[['Close', 'SMA50', 'SMA200']])

    else:
        st.error(f"No data available for {stock.upper()}. Please try a different stock symbol.")
