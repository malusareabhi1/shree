import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

# Trade log to store trade details
trade_log = []

def read_csv_data(uploaded_file):
    try:
        # Read CSV data into DataFrame
        data = pd.read_csv(uploaded_file)
        
        # Ensure the Date column is parsed as a datetime object
        data['Date'] = pd.to_datetime(data['Date'])
        data.set_index('Date', inplace=True)

        # Ensure correct column names for OHLCV
        expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in expected_columns):
            raise ValueError("⚠️ Missing required columns in CSV. Ensure you have Open, High, Low, Close, and Volume columns.")

        data.dropna(inplace=True)  # Drop rows with missing data
        return data

    except Exception as e:
        st.error(f"⚠️ Error reading the CSV: {e}")
        return pd.DataFrame()

def check_crossing(data):
    if 'Close' not in data.columns:
        raise KeyError("❌ 'Close' column is missing in the DataFrame!")

    # Calculate 20‑period SMA
    data['SMA_20'] = data['Close'].rolling(window=20).mean()

    # Drop rows where SMA is NaN (first 19 rows)
    data.dropna(subset=['SMA_20'], inplace=True)

    # Mark crossings
    data['crossed'] = (data['Close'] > data['SMA_20']).astype(int)
    return data

def check_iv(data, iv_threshold=16):
    # Mock IV — replace with real API call if available
    data['IV'] = 17
    data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
    return data

def execute_trade(data):
    for i in range(1, len(data)):
        if data['crossed'].iat[i] == 1 and data['iv_check'].iat[i] == 1:
            entry = data['Close'].iat[i]
            sl = entry * 0.90
            tg = entry * 1.05
            entry_time = data.index[i]
            
            # Log the trade details
            trade_log.append({
                'Entry Time': entry_time,
                'Entry Price': entry,
                'Stop Loss': sl,
                'Target Price': tg,
                'Status': 'Open'
            })
            
            st.success(f"✅ Trade @ ₹{entry:.2f}  SL: ₹{sl:.2f}  TG: ₹{tg:.2f}")
            return entry, sl, tg, entry_time
    st.info("ℹ️ No trade signal.")
    return None, None, None, None

def manage_risk(entry, sl, tg, data):
    for price in data['Close']:
        if price >= tg:
            st.success(f"🎯 Target hit @ ₹{price:.2f}")
            close_trade('Target Hit')
            return True
        if price <= sl:
            st.error(f"🛑 SL hit @ ₹{price:.2f}")
            close_trade('Stop Loss Hit')
            return True
    return False

def close_trade(status):
    # Update the last trade in the log to "Closed"
    if trade_log:
        trade_log[-1]['Status'] = status

# --- Streamlit UI ---
st.title("📊 Doctor Trade Strategy")

# Sidebar inputs
uploaded_file = st.sidebar.file_uploader("Upload OHLCV CSV File", type=["csv"])

# Handle CSV file upload
if uploaded_file is not None:
    # Read data from CSV
    df = read_csv_data(uploaded_file)
    if not df.empty:
        st.subheader("Raw Data")
        st.dataframe(df.tail(20))

        try:
            df = check_crossing(df)
            df = check_iv(df)

            # Plot
            fig = go.Figure([
                go.Candlestick(x=df.index,
                               open=df['Open'], high=df['High'],
                               low=df['Low'],   close=df['Close']),
                go.Scatter(     x=df.index,
                               y=df['SMA_20'],
                               mode='lines',
                               name='20 SMA')
            ])
            fig.update_layout(title="OHLCV Data with 20 SMA", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # Trade logic
            entry, sl, tg, t0 = execute_trade(df)
            if entry is not None:
                if manage_risk(entry, sl, tg, df):
                    st.info("🔁 Trade Closed (SL/TG hit)")

        except Exception as e:
            st.error(f"❌ Strategy error: {e}")

        # Display trade log
        if trade_log:
            st.subheader("Trade Log")
            trade_df = pd.DataFrame(trade_log)
            st.dataframe(trade_df)

else:
    st.warning("⚠️ Please upload a CSV file.")
