import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# Function to fetch historical stock data
def fetch_data(stock_symbol, start_date, end_date, interval="5m"):
    try:
        # Fetching stock data
        data = yf.download(stock_symbol, start=start_date, end=end_date, interval=interval)
        data = data.dropna()  # Drop rows with NaN values
        return data
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return pd.DataFrame()

# Function to apply the crossing logic based on 20-period SMA
def check_crossing(data):
    # Debugging: Show first few rows and columns
    st.write("Debug: Checking available columns and first few rows of the data:")
    st.write(data.head())
    st.write("Columns:", data.columns.tolist())

    if 'Close' not in data.columns:
        raise KeyError("❌ 'Close' column is missing in the DataFrame!")

    # Check if Close column has NaN values and handle them
    st.write("Debug: Checking for NaN values in 'Close' column")
    st.write(data['Close'].isna().sum())  # Display how many NaN values in 'Close'

    # Drop NaN values from Close column before calculating SMA
    data = data.dropna(subset=['Close'])

    if data['Close'].empty:
        raise ValueError("❌ 'Close' column has no valid data after dropping NaNs!")

    # Calculate the 20-period Simple Moving Average (SMA)
    data['SMA_20'] = data['Close'].rolling(window=20).mean()

    # Debugging: Check if the SMA_20 column is created correctly
    st.write("Debug: First few rows after SMA_20 calculation:")
    st.write(data[['Close', 'SMA_20']].head())

    # Check if SMA_20 is valid
    if 'SMA_20' not in data.columns or data['SMA_20'].isna().all():
        raise ValueError("❌ 'SMA_20' column has all NaN values!")

    # Drop rows with NaN values in SMA_20
    data = data.dropna(subset=['SMA_20'])

    # Adding crossing logic (1 if price is above SMA_20, else 0)
    data['crossed'] = (data['Close'] > data['SMA_20']).astype(int)

    return data

# Function to check the Implied Volatility (IV) condition
def check_iv(data, iv_threshold=16):
    data['IV'] = 17  # Mock IV value (replace with real IV data from an API)
    data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
    return data

# Function to execute the trade based on crossing and IV condition
def execute_trade(data):
    for i in range(1, len(data)):
        if data['crossed'][i] == 1 and data['iv_check'][i] == 1:
            entry_price = data['Close'][i]
            stop_loss = entry_price * (1 - 0.10)  # 10% stop loss
            profit_target = entry_price * (1 + 0.05)  # 5% profit target
            entry_time = data.index[i]  # Capture the entry time
            st.success(f"✅ Trade Executed at {entry_price}, SL: {stop_loss}, Target: {profit_target}")
            return entry_price, stop_loss, profit_target, entry_time
    return None, None, None, None

# Function for risk management (checking stop loss or profit target)
def manage_risk(entry_price, stop_loss, profit_target, data):
    for i in range(len(data)):
        if data['Close'][i] >= profit_target:
            st.success(f"🎯 Profit Target hit at {data['Close'][i]}")
            return True  # Profit booked
        elif data['Close'][i] <= stop_loss:
            st.error(f"🛑 Stop Loss hit at {data['Close'][i]}")
            return True  # Stop loss hit
    return False  # No exit yet

# Streamlit UI setup
st.title("📊 Doctor Trade Strategy")

# Sidebar for user inputs
stock_symbol = st.selectbox("📈 Select Stock Symbol", ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"])
start_date = st.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=10))
end_date = st.date_input("📅 End Date", datetime.date.today())
interval = st.selectbox("⏱ Select Data Interval", ["1m", "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1d"])

# Button to fetch data and run strategy
if st.button("🚀 Fetch Data and Run Strategy"):
    data = fetch_data(stock_symbol, start_date, end_date, interval)

    if data.empty:
        st.warning("⚠️ No data fetched. Please check your date range (max last 60 days) and symbol.")
    else:
        st.subheader("📋 Raw Data Preview")
        st.dataframe(data.tail(20))  # Show last 20 rows of the fetched data

        try:
            # Apply strategy logic: crossing and IV check
            data = check_crossing(data)
            data = check_iv(data)

            # Plot the candlestick chart with SMA
            fig = go.Figure(data=[go.Candlestick(x=data.index,
                                                 open=data['Open'],
                                                 high=data['High'],
                                                 low=data['Low'],
                                                 close=data['Close'],
                                                 name='Candlestick'),
                                  go.Scatter(x=data.index, y=data['SMA_20'], mode='lines', name='20 SMA')])

            fig.update_layout(title=f"{stock_symbol} - {interval} Chart", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig)

            # Execute trade based on strategy logic
            entry_price, stop_loss, profit_target, entry_time = execute_trade(data)

            if entry_price:
                st.write(f"💡 Entry: {entry_price}, Stop Loss: {stop_loss}, Profit Target: {profit_target}")

                # Manage risk and check for exit
                if manage_risk(entry_price, stop_loss, profit_target, data):
                    st.info("🔁 Trade Closed (Risk Management)")

        except Exception as e:
            st.error(f"❌ Error during strategy logic: {e}")
