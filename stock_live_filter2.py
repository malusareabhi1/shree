import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.sidebar.title("📊 Trading Strategy Dashboard")

# Sidebar Inputs
stock = st.sidebar.selectbox("Select Stock", ["^NSEI", "RELIANCE.NS", "TCS.NS", "INFY.NS"])
chart_type = st.sidebar.selectbox("Select Chart Type", ["Candlestick", "Line"])
capital = st.sidebar.number_input("Initial Capital (₹)", min_value=1000, value=100000, step=1000)
daily_limit = st.sidebar.number_input("Daily Trade Limit", min_value=1, value=5)
trade_start = st.sidebar.time_input("Trade Start Time", value=datetime.strptime("09:30", "%H:%M").time())
trade_end = st.sidebar.time_input("Trade Stop Time", value=datetime.strptime("14:30", "%H:%M").time())
lot_qty = st.sidebar.number_input("Lot Quantity", min_value=1, value=1)
interval = st.sidebar.selectbox("Select Time Frame", ["5m", "15m", "1h", "1d"])
order_type = st.sidebar.selectbox("Order Type", ["Market", "Limit"])

st.sidebar.markdown("---")
stop_loss = st.sidebar.slider("Stop Loss (%)", 0.5, 10.0, 1.0)
profit_target = st.sidebar.slider("Profit Target (%)", 0.5, 10.0, 2.0)
trailing_sl = st.sidebar.slider("Trailing Stop Loss (%)", 0.1, 5.0, 0.5)

time_exit = st.sidebar.checkbox("Enable Time-Based Exit")
exit_minutes = st.sidebar.slider("Exit After (Minutes)", 1, 60, 10)

run = st.sidebar.button("▶️ Run Strategy")

# Main layout
st.title(f"{stock} - {interval} Chart")

if run:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)

    df = yf.download(stock, start=start_date, end=end_date, interval=interval)
    if df.empty:
        st.warning("No data found. Please select a valid stock or time frame.")
    else:
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
        df.dropna(inplace=True)

        # Signal: EMA20 Crossover
        df['Signal'] = (df['Close'] > df['EMA20']) & (df['Close'].shift(1) <= df['EMA20'].shift(1))

        # Backtest logic
        trades = []
        capital_remaining = capital
        equity_curve = [capital]
        daily_trades = 0

        for i in range(1, len(df)):
            if df['Signal'].iloc[i] and daily_trades < daily_limit:
                entry_time = df.index[i]
                entry_price = df['Close'].iloc[i]
                stop_price = entry_price * (1 - stop_loss / 100)
                target_price = entry_price * (1 + profit_target / 100)

                # Mock exit after a few bars or target hit
                exit_index = min(i + 3, len(df) - 1)
                exit_price = df['Close'].iloc[exit_index]
                exit_time = df.index[exit_index]

                if exit_price <= stop_price:
                    exit_price = stop_price
                elif exit_price >= target_price:
                    exit_price = target_price

                profit = (exit_price - entry_price) * lot_qty
                capital_remaining += profit
                equity_curve.append(capital_remaining)
                trades.append({
                    "Entry Time": entry_time,
                    "Entry Price": round(entry_price, 2),
                    "Exit Time": exit_time,
                    "Exit Price": round(exit_price, 2),
                    "Profit (₹)": round(profit, 2)
                })
                daily_trades += 1

        # Show data and signals
        st.markdown("### 🔍 Raw Data & Signal")
        st.dataframe(df.tail(20))

        st.markdown("### 📉 Chart with Signals")

        fig = go.Figure()
        if chart_type == "Candlestick":
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Candles"
            ))
        else:
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name='Close', line=dict(color='blue')))

        fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='EMA20', line=dict(color='orange')))
        
        signal_points = df[df['Signal']]
        fig.add_trace(go.Scatter(
            x=signal_points.index,
            y=signal_points['Close'],
            mode='markers',
            name='Buy Signal',
            marker=dict(color='green', symbol='triangle-up', size=10)
        ))

        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # Trade Log
        st.markdown("### 💼 Trade Log")
        if trades:
            st.dataframe(pd.DataFrame(trades))
        else:
            st.info("No trades generated in the selected time frame.")

        # Equity Curve
        st.markdown("### 📈 Equity Curve")
        st.line_chart(equity_curve)
