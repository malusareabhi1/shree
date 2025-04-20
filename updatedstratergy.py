import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# Define functions for the strategy logic
def fetch_data(stock_symbol, start_date, end_date, interval="5m"):
    try:
        data = yf.download(stock_symbol, start=start_date, end=end_date, interval=interval)
        data = data.dropna()  # Drop any rows with NaN values
        return data
    except Exception as e:
        st.error(f"⚠️ Error fetching data: {e}")
        return pd.DataFrame()

def check_crossing(data):
    if 'Close' not in data.columns:
        raise KeyError("❌ 'Close' column is missing in the DataFrame!")

    if data['Close'].dropna().empty:
        raise ValueError("❌ 'Close' column has no valid data (all values are NaN)!")

    # Calculate 20-period SMA and check if it's calculated correctly
    data['SMA_20'] = data['Close'].rolling(window=20).mean()

    if data['SMA_20'].isna().all():
        raise ValueError("❌ 'SMA_20' column has no valid data (all NaNs)!")

    # Drop rows with NaN in SMA_20
    data = data.dropna(subset=['SMA_20'])

    # Add crossing logic
    data['crossed'] = (data['Close'] > data['SMA_20']).astype(int)

    return data

def check_iv(data, iv_threshold=16):
    data['IV'] = 17  # Mock IV value (replace with actual IV data from API)
    data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
    return data

def execute_trade(data):
    for i in range(1, len(data)):
        if data['crossed'][i] == 1 and data['iv_check'][i] == 1:
            entry_price = data['Close'][i]
            stop_loss = entry_price * (1 - 0.10)
            profit_target = entry_price * (1 + 0.05)
            entry_time = data.index[i]
            st.success(f"✅ Trade Executed at {entry_price}, SL: {stop_loss}, Target: {profit_target}")
            return entry_price, stop_loss, profit_target, entry_time
    return None, None, None, None

def manage_risk(entry_price, stop_loss, profit_target, data):
    for i in range(len(data)):
        if data['Close'][i] >= profit_target:
            st.success(f"🎯 Profit Target hit at {data['Close'][i]}")
            return True
        elif data['Close'][i] <= stop_loss:
            st.error(f"🛑 Stop Loss hit at {data['Close'][i]}")
            return True
    return False

def time_based_exit(entry_time, data, max_time=10):
    if entry_time is None:
        return False
    time_elapsed = (data.index[-1] - entry_time).total_seconds() / 60
    if time_elapsed >= max_time:
        st.warning(f"⏰ Time-based exit after {max_time} minutes")
        return True
    return False

# Streamlit UI
st.title("📊 Doctor Trade Strategy (Customizable Time Frame)")

# Sidebar inputs
stock_symbol = st.selectbox("📈 Select Stock Symbol", ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"])
start_date = st.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=10))
end_date = st.date_input("📅 End Date", datetime.date.today())

# Interval input
interval = st.selectbox("⏱ Select Data Interval", ["1m", "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1d"])

if st.button("🚀 Fetch Data and Run Strategy"):
    data = fetch_data(stock_symbol, start_date, end_date, interval)

    if data.empty:
        st.warning("⚠️ No data fetched. Please check your date range (max last 60 days) and symbol (use NSE stock symbols ending with '.NS').")
    else:
        st.subheader("📋 Raw Data Preview")
        st.dataframe(data.tail(20))  # show last 20 rows

        try:
            data = check_crossing(data)
            data = check_iv(data)

            # Plot chart
            fig = go.Figure(data=[go.Candlestick(x=data.index,
                                                 open=data['Open'],
                                                 high=data['High'],
                                                 low=data['Low'],
                                                 close=data['Close'],
                                                 name='Candlestick'),
                                  go.Scatter(x=data.index, y=data['SMA_20'], mode='lines', name='20 SMA')])
            fig.update_layout(title=f"{stock_symbol} - {interval} Chart", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig)

            # Trade logic
            entry_price, stop_loss, profit_target, entry_time = execute_trade(data)

            if entry_price:
                st.write(f"💡 Entry: {entry_price}, SL: {stop_loss}, Target: {profit_target}")

                if manage_risk(entry_price, stop_loss, profit_target, data):
                    st.info("🔁 Trade Closed (Risk Management)")

                elif time_based_exit(entry_time, data):
                    st.info("⏳ Trade Closed (Time-based Exit)")

            else:
                st.info("⚠️ No valid trade signal found in this range.")

        except Exception as e:
            st.error(f"❌ Error during strategy logic: {e}")
