import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# Step 1: Fetch historical data
def fetch_data(stock_symbol, start_date, end_date):
    try:
        data = yf.download(stock_symbol, start=start_date, end=end_date, interval="5m", progress=False)
        if data.empty:
            st.warning("⚠️ No data fetched. Please check your date range or symbol.")
            return pd.DataFrame()
        data.dropna(inplace=True)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Step 2: Calculate SMA and detect crossover
def check_crossing(data):
    if 'Close' not in data.columns:
        raise KeyError("❌ 'Close' column is missing in the data.")
    if data['Close'].dropna().empty:
        raise ValueError("❌ 'Close' column has all NaN values.")

    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data.dropna(subset=['SMA_20'], inplace=True)
    data['crossed'] = (data['Close'] > data['SMA_20']).astype(int)
    return data

# Step 3: Add Implied Volatility (mock)
def check_iv(data, iv_threshold=16):
    data['IV'] = 17  # Mock constant IV
    data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
    return data

# Step 4: Execute trade if conditions are met
def execute_trade(data):
    for i in range(1, len(data)):
        if data['crossed'].iloc[i] == 1 and data['iv_check'].iloc[i] == 1:
            entry_price = data['Close'].iloc[i]
            stop_loss = entry_price * (1 - 0.10)
            profit_target = entry_price * (1 + 0.05)
            entry_time = data.index[i]
            st.success(f"✅ Trade Executed at ₹{entry_price:.2f} | SL: ₹{stop_loss:.2f} | Target: ₹{profit_target:.2f}")
            return entry_price, stop_loss, profit_target, entry_time
    st.info("No trade executed based on current conditions.")
    return None, None, None, None

# Step 5: Manage risk
def manage_risk(entry_price, stop_loss, profit_target, data):
    for i in range(len(data)):
        price = data['Close'].iloc[i]
        if price >= profit_target:
            st.success(f"🎯 Profit Target hit at ₹{price:.2f}. Book Profit!")
            return True
        elif price <= stop_loss:
            st.error(f"🛑 Stop Loss hit at ₹{price:.2f}. Exit Trade!")
            return True
    return False

# Step 6: Time-based exit
def time_based_exit(entry_time, data, max_minutes=10):
    if not entry_time:
        return False
    last_time = data.index[-1]
    elapsed_minutes = (last_time - entry_time).total_seconds() / 60
    if elapsed_minutes >= max_minutes:
        st.warning(f"⌛ Time-based exit after {max_minutes} minutes.")
        return True
    return False

# Streamlit UI
st.set_page_config(page_title="Doctor Trade Strategy", layout="wide")
st.title("💉 Doctor Trade Strategy (5-Minute Chart)")

stock_symbol = st.selectbox("📈 Select Symbol", ["^NSEI", "^NSEBANK"], index=0)
start_date = st.date_input("Start Date", datetime.date(2023, 1, 1))
end_date = st.date_input("End Date", datetime.date(2023, 12, 31))

fetch_btn = st.button("📥 Fetch Data")

if fetch_btn:
    if start_date >= end_date:
        st.error("⚠️ Start date must be before end date.")
    else:
        data = fetch_data(stock_symbol, start_date, end_date)
        if not data.empty:
            try:
                data = check_crossing(data)
                data = check_iv(data)

                # Plot chart
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'],
                    name='Candlestick'
                ))
                fig.add_trace(go.Scatter(
                    x=data.index, y=data['SMA_20'],
                    mode='lines', name='SMA 20',
                    line=dict(color='orange')
                ))
                fig.update_layout(title=f"{stock_symbol} | Candlestick with 20 SMA",
                                  xaxis_title="Time", yaxis_title="Price",
                                  xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # Show data
                with st.expander("📊 Show DataFrame"):
                    st.dataframe(data.tail(50), use_container_width=True)

                # Execute trade logic
                entry_price, stop_loss, profit_target, entry_time = execute_trade(data)
                if entry_price:
                    if manage_risk(entry_price, stop_loss, profit_target, data):
                        st.info("🔁 Trade Closed via Risk Management.")
                    elif time_based_exit(entry_time, data):
                        st.info("⏳ Trade Closed via Time Exit.")
            except Exception as e:
                st.error(f"🚫 Strategy Error: {e}")
