import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Step 1: Streamlit App Configuration
st.set_page_config("📊 New Nifty Strategy Backtest", layout="centered")
st.title("📊 New Nifty Strategy - Backtest")

# Step 2: CSV Upload
uploaded_file = st.file_uploader("📂 Upload CSV file", type="csv")

# Step 3: Load Data
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Data loaded successfully")

    # Step 4: Data Preprocessing
    # Assuming the data has columns: 'Date', 'Open', 'High', 'Low', 'Close'
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    # Calculate 20 SMA
    df['20_SMA'] = df['Close'].rolling(window=20).mean()

    # Add Bollinger Bands (Upper, Middle, and Lower)
    df['Upper_Band'] = df['20_SMA'] + 2 * df['Close'].rolling(window=20).std()
    df['Lower_Band'] = df['20_SMA'] - 2 * df['Close'].rolling(window=20).std()

    # Display preprocessed data
    st.dataframe(df.tail())

    # Strategy Variables
    stop_loss_pct = 0.10  # 10% Stop Loss
    profit_target_pct = 0.05  # 5% Profit Target
    trailing_stop_pct = 0.04  # 4% Trailing Stop

    # Backtest the strategy
    trades = []  # to hold the trade details
    capital = 50000
    qty = 10
    position_open = False
    entry_price = 0
    trailing_stop = 0
    stop_loss_price = 0
    profit_target_price = 0
    time_in_trade = 0
    reference_candle = None
    exit_reason = ""

    for idx, row in df.iterrows():
        # Check if the market is open between 9:30 AM to 1:30 PM
        #if row.name.time() >= datetime.strptime("09:30:00", "%H:%M:%S").time() and row.name.time() <= datetime.strptime("14:30:00", "%H:%M:%S").time():
            
            if position_open:
                time_in_trade += 1

                # Stop loss condition
                if row['Close'] <= stop_loss_price:
                    exit_reason = "Stop Loss Hit"
                    position_open = False
                    trades.append({
                        'Action': 'SELL',
                        'Price': row['Close'],
                        'Exit Reason': exit_reason,
                        'Time': idx,
                    })
                    capital += qty * (row['Close'] - entry_price)  # update capital based on stop loss
                    st.write(f"Trade closed due to {exit_reason} at {row['Close']}")
                    continue

                # Profit target condition
                elif row['Close'] >= profit_target_price:
                    exit_reason = "Profit Target Hit"
                    position_open = False
                    trades.append({
                        'Action': 'SELL',
                        'Price': row['Close'],
                        'Exit Reason': exit_reason,
                        'Time': idx,
                    })
                    capital += qty * (row['Close'] - entry_price)  # update capital based on profit target
                    st.write(f"Trade closed due to {exit_reason} at {row['Close']}")
                    continue

                # Trailing stop condition
                if row['Close'] > entry_price * (1 + trailing_stop_pct):
                    trailing_stop_price = entry_price * (1 + trailing_stop_pct)
                    st.write(f"Trailing Stop updated to {trailing_stop_price}")

                # Time-based exit after 10 minutes
                if time_in_trade > 10:
                    exit_reason = "Time-Based Exit"
                    position_open = False
                    trades.append({
                        'Action': 'SELL',
                        'Price': row['Close'],
                        'Exit Reason': exit_reason,
                        'Time': idx,
                    })
                    capital += qty * (row['Close'] - entry_price)  # update capital based on time-based exit
                    st.write(f"Trade closed due to {exit_reason} at {row['Close']}")
                    continue

            # Entry Condition (20 SMA Cross & Reference Candle Conditions)
            if row['Close'] > row['20_SMA'] and row['Close'] > row['Upper_Band']:
                # Check previous candle for reference conditions
                if reference_candle is not None:
                    if row['Close'] > reference_candle['Close']:
                        entry_price = row['Close']
                        stop_loss_price = entry_price * (1 - stop_loss_pct)
                        profit_target_price = entry_price * (1 + profit_target_pct)
                        position_open = True
                        reference_candle = row
                        trades.append({
                            'Action': 'BUY',
                            'Price': entry_price,
                            'Time': idx,
                        })
                        st.write(f"Trade opened at {entry_price} due to conditions")

        #else:
            #st.warning("Market closed, no trades will be made outside 9:30 AM to 1:30 PM")

    # Step 5: Display Results
    st.write(f"Total Capital after Backtest: ₹{capital}")
    st.dataframe(pd.DataFrame(trades))

    # Step 6: Visualize Trades on the Chart
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Candlesticks',
    )])

    # Add buy signals
    for trade in trades:
        if trade['Action'] == 'BUY':
            fig.add_trace(go.Scatter(
                x=[trade['Time']],
                y=[trade['Price']],
                mode='markers',
                marker=dict(symbol='triangle-up', color='green', size=10),
                name='Buy Signal',
            ))

    # Add sell signals
    for trade in trades:
        if trade['Action'] == 'SELL':
            fig.add_trace(go.Scatter(
                x=[trade['Time']],
                y=[trade['Price']],
                mode='markers',
                marker=dict(symbol='triangle-down', color='red', size=10),
                name='Sell Signal',
            ))

    fig.update_layout(
        title="Trade Entry/Exit Visualized",
        xaxis_title="Date",
        yaxis_title="Price (₹)",
        template="plotly_dark",
        hovermode='x unified',
    )

    st.plotly_chart(fig)

else:
    st.warning("📴 Please upload a valid CSV file to backtest the strategy.")
