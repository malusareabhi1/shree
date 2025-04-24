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

# Run button
run = st.sidebar.button("▶️ Run Strategy")

# Main layout
st.title(f"{stock} - {interval} Chart")

if run:
    # Fetch past 2 days of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2)

    df = yf.download(stock, start=start_date, end=end_date, interval=interval)
    if df.empty:
        st.warning("No data found. Please select a valid stock or time frame.")
    else:
        df.dropna(inplace=True)
        df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

        # Show raw data
        st.dataframe(df.tail(20))

        # Chart Title
        st.markdown(f"### 📉 {interval} Candle Chart with 20 EMA")

        if chart_type == "Candlestick":
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name="Candles"
            ))
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['EMA20'],
                line=dict(color='orange', width=1),
                name='EMA 20'
            ))
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['Close'],
                line=dict(color='blue'),
                name='Close Price'
            ))
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['EMA20'],
                line=dict(color='orange', width=1),
                name='EMA 20'
            ))

        fig.update_layout(
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
