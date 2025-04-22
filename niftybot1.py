import streamlit as st
import pandas as pd
import numpy as np
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

# Option to enable/disable time-based exit
#enable_time_exit = st.sidebar.checkbox("Enable Time-Based Exit", value=True)
enable_time_exit = st.sidebar.checkbox("Enable Time-Based Exit", value=True)
exit_minutes = st.sidebar.number_input("Exit After X Minutes", min_value=1, max_value=60, value=10)

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
                if row['Close'] <= stop_loss_price:
                    exit_reason = "Stop Loss Hit"
                elif row['Close'] >= profit_target_price:
                    exit_reason = "Profit Target Hit"
                elif row['Close'] < trailing_stop and trailing_stop > 0:
                    exit_reason = "Trailing Stop Hit"
                #elif enable_time_exit and (idx - entry_time) > timedelta(minutes=10):
                elif enable_time_exit and (idx - entry_time) > timedelta(minutes=exit_minutes):
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

    final_capital = cumulative_pnl[-1] if cumulative_pnl else capital
    st.write(f"💰 Final Capital: ₹{final_capital:,.2f}")

    trade_df = pd.DataFrame(trades)

    if not trade_df.empty:
        st.subheader("📋 Trade Log")
        st.dataframe(trade_df)

        csv = trade_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Trade Log as CSV",
            data=csv,
            file_name='trade_log.csv',
            mime='text/csv',
        )

        # 📉 Strategy Execution Chart
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

        # 📈 Cumulative PnL Chart
        trade_df['Cumulative Capital'] = trade_df['Capital'].ffill()
        pnl_fig = go.Figure()
        pnl_fig.add_trace(go.Scatter(
            x=trade_df['Time'],
            y=trade_df['Cumulative Capital'],
            mode='lines+markers',
            line=dict(color='gold', width=2),
            name='Cumulative Capital'
        ))
        pnl_fig.update_layout(
            title="📈 Cumulative Capital Over Time",
            xaxis_title="Date",
            yaxis_title="Capital (₹)",
            template="plotly_dark"
        )
        st.plotly_chart(pnl_fig)

        # 📊 Performance Summary
        buy_trades = trade_df[trade_df['Action'] == 'BUY']
        sell_trades = trade_df[trade_df['Action'] == 'SELL']

        total_trades = len(sell_trades)
        winning_trades = sell_trades[sell_trades['PnL'] > 0].shape[0]
        losing_trades = sell_trades[sell_trades['PnL'] <= 0].shape[0]
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        max_drawdown = trade_df['Cumulative Capital'].cummax() - trade_df['Cumulative Capital']
        max_drawdown = max_drawdown.max() if not max_drawdown.empty else 0

        # Count exit reasons
        exit_reasons = sell_trades['Exit Reason'].value_counts().to_dict()
        time_based_exits = exit_reasons.get("Time-Based Exit", 0)

        summary_df = pd.DataFrame({
            "Metric": [
                "Total Trades",
                "Winning Trades",
                "Losing Trades",
                "Win Rate (%)",
                "Max Drawdown (₹)",
                "Time-Based Exits"
            ],
            "Value": [
                total_trades,
                winning_trades,
                losing_trades,
                f"{win_rate:.2f}",
                f"{max_drawdown:,.2f}",
                time_based_exits
            ]
        })

        st.subheader("📊 Performance Summary")
        st.table(summary_df)

        st.subheader("📌 Exit Reason Breakdown")
        exit_reason_df = pd.DataFrame(list(exit_reasons.items()), columns=["Exit Reason", "Count"])
        st.table(exit_reason_df)

    else:
        st.warning("🚫 No trades were executed based on the given conditions.")
else:
    st.warning("📴 Please upload a valid CSV file to backtest the strategy.")
