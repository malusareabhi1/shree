import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# Define functions for the strategy logic

# Step 1: Fetch historical data for Nifty
def fetch_data(stock_symbol, start_date, end_date):
    data = yf.download(stock_symbol, start=start_date, end=end_date, interval="5m")
    data = data.dropna()  # Drop missing values to ensure clean data
    return data

# Step 2: Check for Crossing of the Center Line (20 SMA)
def check_crossing(data):
    # Calculate 20-period SMA
    data['SMA_20'] = data['Close'].rolling(window=20).mean()

    # Print columns and inspect data for debugging
    print("Columns after SMA calculation:", data.columns)
    print(data.head())  # Print first few rows to inspect 'SMA_20'

    # Check if 'SMA_20' exists
    if 'SMA_20' not in data.columns:
        raise KeyError("'SMA_20' column not found after calculation.")

    # Drop rows where 'SMA_20' is NaN (due to rolling window)
    data = data.dropna(subset=['SMA_20'])

    # Perform the crossing check
    data['crossed'] = np.where(data['Close'] > data['SMA_20'], 1, 0)
    return data



# Step 3: Add Implied Volatility check
def check_iv(data, iv_threshold=16):
    # For this example, assume IV data is fetched from a separate function or API
    data['IV'] = 17  # Mock IV data; in reality, you'd get it from the API
    data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
    return data

# Step 4: Trade Execution
def execute_trade(data):
    for i in range(1, len(data)):
        if data['crossed'][i] == 1 and data['iv_check'][i] == 1:
            entry_price = data['Close'][i]
            stop_loss = entry_price * (1 - 0.10)  # 10% stop loss
            profit_target = entry_price * (1 + 0.05)  # 5% profit target
            entry_time = data.index[i]  # Capture the time when the trade is executed
            st.write(f"Trade Executed at {entry_price}, SL: {stop_loss}, Target: {profit_target}")
            return entry_price, stop_loss, profit_target, entry_time
    return None, None, None, None

# Step 5: Profit Booking and Stop Loss Adjustment
def manage_risk(entry_price, stop_loss, profit_target, data):
    for i in range(len(data)):
        if data['Close'][i] >= profit_target:
            st.write(f"Profit Target hit at {data['Close'][i]}. Book Profit!")
            return True  # Profit booked
        elif data['Close'][i] <= stop_loss:
            st.write(f"Stop Loss hit at {data['Close'][i]}. Exit Trade!")
            return True  # Stop loss hit
    return False  # No exit

# Step 6: Time-based Exit (After 10 minutes)
def time_based_exit(entry_time, data, max_time=10):
    time_elapsed = (data.index[-1] - entry_time).total_seconds() / 60
    if time_elapsed >= max_time:
        st.write(f"Time-based exit after {max_time} minutes. Exit trade!")
        return True
    return False

# Streamlit UI

# Page setup
st.title("Doctor Trade Strategy (5-Minute Time Frame)")

# User inputs
stock_symbol = st.selectbox("Select Stock", ["^NSEBANK", "^NSEI"])  # Nifty or BankNifty
start_date = st.date_input("Start Date", datetime.date(2023, 1, 1))
end_date = st.date_input("End Date", datetime.date(2023, 12, 31))

# Fetch data
data = fetch_data(stock_symbol, start_date, end_date)

# Add technical indicators
data = check_crossing(data)
data = check_iv(data)

# Plot data
fig = go.Figure(data=[go.Candlestick(x=data.index,
                                    open=data['Open'],
                                    high=data['High'],
                                    low=data['Low'],
                                    close=data['Close'],
                                    name='Candlestick'),
                     go.Scatter(x=data.index, y=data['SMA_20'], mode='lines', name='20 SMA')])

fig.update_layout(title=f"{stock_symbol} Price Chart", xaxis_title="Date", yaxis_title="Price")
st.plotly_chart(fig)

# Execute trade logic
entry_price, stop_loss, profit_target, entry_time = execute_trade(data)

if entry_price:
    st.write(f"Entry Price: {entry_price}, Stop Loss: {stop_loss}, Profit Target: {profit_target}")

    # Manage risk and check for exit
    if manage_risk(entry_price, stop_loss, profit_target, data):
        st.write("Trade Closed")

    # Time-based exit after 10 minutes
    if time_based_exit(entry_time, data):
        st.write("Trade Closed due to Time-based Exit")
