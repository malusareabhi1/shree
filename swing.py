import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objs as go
from datetime import datetime

# --- Calculate Bollinger Bands ---
def calculate_bollinger_bands(df, window=20, num_std_dev=2):
    rolling_mean = df['Close'].rolling(window=window).mean()
    rolling_std = df['Close'].rolling(window=window).std()
    
    df['Upper_Band'] = rolling_mean + (rolling_std * num_std_dev)
    df['Lower_Band'] = rolling_mean - (rolling_std * num_std_dev)
    df['Middle_Band'] = rolling_mean
    return df

# --- Calculate RSI ---
def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- Swing Trading Strategy Function ---
def swing_trading_strategy(df, rsi_period=14, bb_period=20, bb_std_dev=2, sma_period=50):
    # Calculate Bollinger Bands
    df = calculate_bollinger_bands(df, window=bb_period, num_std_dev=bb_std_dev)
    
    # Calculate 50-period SMA
    df['50_SMA'] = df['Close'].rolling(window=sma_period).mean()
    
    # Calculate RSI
    df = calculate_rsi(df, period=rsi_period)
    
    # Initialize columns
    df['Signal'] = 0
    df['Position'] = 0
    df['Stop_Loss'] = np.nan
    df['Target'] = np.nan
    
    # Long entry condition
    df.loc[(df['Close'] > df['50_SMA']) & 
           (df['Close'] < df['Lower_Band']) & 
           (df['RSI'] > 30), 'Signal'] = 1  # Buy signal
    
    # Short entry condition
    df.loc[(df['Close'] < df['50_SMA']) & 
           (df['Close'] > df['Upper_Band']) & 
           (df['RSI'] < 70), 'Signal'] = -1  # Sell signal
    
    # Implement stop loss and take profit
    for i in range(1, len(df)):
        if df['Signal'].iloc[i] == 1:  # Buy position
            df['Stop_Loss'].iloc[i] = df['Close'].iloc[i] * 0.98  # 2% stop loss
            df['Target'].iloc[i] = df['Close'].iloc[i] * 1.05  # 5% profit target
        elif df['Signal'].iloc[i] == -1:  # Short position
            df['Stop_Loss'].iloc[i] = df['Close'].iloc[i] * 1.02  # 2% stop loss
            df['Target'].iloc[i] = df['Close'].iloc[i] * 0.95  # 5% profit target

    return df

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("📈 Swing Trading Strategy Dashboard")

# File uploader for CSV file
uploaded_file = st.file_uploader("📁 Upload your 5-minute OHLC CSV file", type=["csv"])

# Input for RSI period
rsi_input = st.slider("⚙️ Set RSI Period", min_value=10, max_value=50, value=14, step=1)

# Input for Bollinger Band Period and Standard Deviation
bb_period_input = st.slider("⚙️ Set Bollinger Band Period", min_value=10, max_value=50, value=20, step=1)
bb_std_dev_input = st.slider("⚙️ Set Bollinger Band Std Dev", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

# Input for 50 SMA period
sma_input = st.slider("⚙️ Set 50 SMA Period", min_value=20, max_value=100, value=50, step=1)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Parse date and set index
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

        # Make sure Date is a datetime object
        if not pd.api.types.is_datetime64_any_dtype(df.index):
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            st.error("CSV must contain: Open, High, Low, Close, Volume")
        else:
            # Apply the trading strategy
            df = swing_trading_strategy(df, 
                                        rsi_period=rsi_input, 
                                        bb_period=bb_period_input, 
                                        bb_std_dev=bb_std_dev_input, 
                                        sma_period=sma_input)
            
            st.subheader("📊 Swing Trading Strategy Chart with Signals")

            # Plot the chart using Plotly
            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Candlestick'))

            # 50 SMA line
            fig.add_trace(go.Scatter(
                x=df.index, y=df['50_SMA'],
                mode='lines', name='50 SMA',
                line=dict(color='orange')))

            # Bollinger Bands
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Upper_Band'],
                mode='lines', name='Upper Band',
                line=dict(color='green', dash='dot')))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Lower_Band'],
                mode='lines', name='Lower Band',
                line=dict(color='red', dash='dot')))
            
            # Plot buy and sell signals
            buy_signals = df[df['Signal'] == 1]
            sell_signals = df[df['Signal'] == -1]

            fig.add_trace(go.Scatter(
                x=buy_signals.index,
                y=buy_signals['Close'],
                mode='markers+text',
                marker=dict(color='lime', size=10, symbol='triangle-up'),
                text=['Buy']*len(buy_signals),
                textposition='top center',
                name='Buy Signal'))

            fig.add_trace(go.Scatter(
                x=sell_signals.index,
                y=sell_signals['Close'],
                mode='markers+text',
                marker=dict(color='red', size=10, symbol='triangle-down'),
                text=['Sell']*len(sell_signals),
                textposition='top center',
                name='Sell Signal'))

            fig.update_layout(xaxis_rangeslider_visible=False, height=650)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 Signal Log")
            # Show trade signals in a dataframe
            if buy_signals.empty and sell_signals.empty:
                st.info("No buy or sell signals found with the current parameters.")
            else:
                st.dataframe(buy_signals[['Open', 'High', 'Low', 'Close', 'Volume']])
                st.download_button(
                    label="💾 Download Buy Signals",
                    data=buy_signals.to_csv().encode(),
                    file_name="buy_signals.csv",
                    mime="text/csv"
                )

                st.dataframe(sell_signals[['Open', 'High', 'Low', 'Close', 'Volume']])
                st.download_button(
                    label="💾 Download Sell Signals",
                    data=sell_signals.to_csv().encode(),
                    file_name="sell_signals.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"❌ Error: {e}")
