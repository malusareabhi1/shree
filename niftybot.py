import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Step 1: Streamlit App Configuration
st.set_page_config("📊 New Nifty Strategy Backtest", layout="centered")
st.title("📊 New Nifty Strategy - Backtest")

# Sidebar for Strategy Parameters
st.sidebar.header("🛠 Strategy Parameters")
stop_loss_pct = st.sidebar.slider("Stop Loss %", 1, 20, 10) / 100
profit_target_pct = st.sidebar.slider("Profit Target %", 1, 20, 5) / 100
trailing_stop_pct = st.sidebar.slider("Trailing Stop %", 1, 10, 4) / 100
initial_capital = st.sidebar.number_input("Initial Capital (₹)", value=50000)
qty = st.sidebar.number_input("Quantity per Trade", value=10)

# Step 2: CSV Upload
uploaded_file = st.file_uploader("📂 Upload CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("✅ Data loaded successfully")

    # Step 3: Data Preprocessing
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    df['20_SMA'] = df['Close'].rolling(window=20).mean()
    df['Upper_Band'] = df['20_SMA'] + 2 * df['Close'].rolling(window=20).std()
    df['Lower_Band'] = df['20_SMA'] - 2 * df['Close'].rolling(window=20).std()

    st.dataframe(df.tail())

    # Strategy Execution
    trades = []
    capital = initial_capital
    position_open = False
    entry_price = 0
    trailing_stop = 0
    stop_loss_price = 0
    profit_target_price = 0
    entry_time = None
    reference_candle = None
    exit_reason = ""

    cumulative_pnl = []

    for idx, row in df.iterrows():
        current_time = idx.time()

        if datetime.strptime("09:30:00", "%H:%M:%S").time() <= current_time <= datetime.strptime("14:30:00", "%H:%M:%S").time():
            if position_open:
                # Check Exit Conditions
                if row['Close'] <= stop_loss_price:
                    exit_reason = "Stop Loss Hit"
                elif row['Close'] >= profit_target_price:
                    exit_reason = "Profit Target Hit"
                elif row['Close'] < trailing_stop and trailing_stop > 0:
                    exit_reason = "Trailing Stop Hit"
                elif (idx - entry_time) > timedelta(minutes=10):
                    exit_reason = "Time-Based Exit"
                else:
                    if row['Close'] > entry_price * (1 + trailing_stop_pct):
                        trailing_stop = row['Close'] * (1 - trailing_stop_pct)
                    continue  # no exit yet

                pnl = qty * (row['Close'] - entry_price)
                capital += pnl
                cumulative_pnl.append(capital)
                trades.append({
                    'Action': 'SELL',
                    'Price': row['Close'],
                    'Exit Reason': exit_reason,
                    'Time': idx,
                    'Capital': capital,
                    'PnL': pnl
                })
                position_open = False
                trailing_stop = 0
                continue

            # Entry Condition
            if row['Close'] > row['20_SMA'] and row['Close'] > row['Upper_Band']:
                if reference_candle is not None and row['Close'] > reference_candle['Close']:
                    entry_price = row['Close']
                    stop_loss_price = entry_price * (1 - stop_loss_pct)
                    profit_target_price = entry_price * (1 + profit_target_pct)
                    trailing_stop = entry_price * (1 - trailing_stop_pct)
                    entry_time = idx
                    position_open = True
                    trades.append({
                        'Action': 'BUY',
                        'Price': entry_price,
                        'Time': idx,
                        'Capital': capital,
                        'PnL': 0
                    })
                reference_candle = row
        else:
            continue

    # Final cumulative PnL tracking
    if cumulative_pnl:
        final_capital = cumulative_pnl[-1]
    else:
        final_capital = capital

    st.write(f"💰 Final Capital: ₹{final_capital:,.2f}")

    trade_df = pd.DataFrame(trades)
    if not trade_df.empty:
        st.subheader("📋 Trade Log")
        st.dataframe(trade_df)

        # Download Button
        csv = trade_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Trade Log as CSV",
            data=csv,
            file_name='trade_log.csv',
            mime='text/csv',
        )

        # Visualization
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Candlesticks'
        )])

        for trade in trades:
            color = 'green' if trade['Action'] == 'BUY' else 'red'
            symbol = 'triangle-up' if trade['Action'] == 'BUY' else 'triangle-down'
            fig.add_trace(go.Scatter(
                x=[trade['Time']],
                y=[trade['Price']],
                mode='markers',
                marker=dict(symbol=symbol, color=color, size=10),
                name=trade['Action']
            ))

        fig.update_layout(
            title="📉 Strategy Execution Chart",
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            template="plotly_dark",
            hovermode="x unified"
        )
        st.plotly_chart(fig)

    else:
        st.warning("🚫 No trades were executed based on the given conditions.")
else:
    st.warning("📴 Please upload a valid CSV file to backtest the strategy.")
