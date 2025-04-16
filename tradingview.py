import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta
import yfinance as yf

# --- Doctor Algo-BOT Strategy Function ---
def doctor_algo_bot_strategy(df, iv_value=16.0):
    df['20_SMA'] = df['Close'].rolling(window=20).mean()
    std_dev = df['Close'].rolling(window=20).std()
    df['Upper_Band'] = df['20_SMA'] + (2 * std_dev)
    df['Lower_Band'] = df['20_SMA'] - (2 * std_dev)
    df['Avg_Volume'] = df['Volume'].rolling(window=20).mean()
    df['Signal'] = 0

    for i in range(21, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        ref_prev = df.iloc[i-2] if i >= 2 else prev

        if (current.name.time() >= datetime.strptime("09:30", "%H:%M").time()
            and prev['Close'] > prev['20_SMA']
            and prev['Low'] > prev['20_SMA']
            and current['Close'] > prev['Close']
            and current['Volume'] > df['Avg_Volume'].iloc[i]
            and iv_value >= 16):

            ref_level = max(ref_prev['High'], prev['Close'])
            if current['Close'] > ref_level:
                df.at[df.index[i], 'Signal'] = 1  # Entry Signal

    return df

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("📈 Doctor Algo-BOT Strategy with Live Stock Selection")

nifty_50_stocks = {
    'Reliance': 'RELIANCE.NS', 'TCS': 'TCS.NS', 'Infosys': 'INFY.NS', 'HDFC Bank': 'HDFCBANK.NS',
    'ICICI Bank': 'ICICIBANK.NS', 'Axis Bank': 'AXISBANK.NS', 'Kotak Bank': 'KOTAKBANK.NS',
    'ITC': 'ITC.NS', 'LT': 'LT.NS', 'SBIN': 'SBIN.NS'
}

selected_stock = st.selectbox("📊 Select a NIFTY 50 Stock", options=list(nifty_50_stocks.keys()))
days = st.slider("📅 Number of past days to fetch", min_value=5, max_value=60, value=15)
iv_input = st.number_input("⚙️ Current IV (Implied Volatility)", min_value=10.0, value=18.0)

if selected_stock:
    try:
        symbol = nifty_50_stocks[selected_stock]
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = yf.download(symbol, start=start_date, end=end_date, interval='5m')
        df.dropna(inplace=True)
        df = doctor_algo_bot_strategy(df.copy(), iv_value=iv_input)

        st.subheader(f"📊 Bollinger Band Breakout Chart for {selected_stock} ({symbol})")

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'],
            name='Candlestick'))

        fig.add_trace(go.Scatter(x=df.index, y=df['20_SMA'], mode='lines', name='20 SMA', line=dict(color='orange')))
        fig.add_trace(go.Scatter(x=df.index, y=df['Upper_Band'], mode='lines', name='Upper Band', line=dict(color='green', dash='dot')))
        fig.add_trace(go.Scatter(x=df.index, y=df['Lower_Band'], mode='lines', name='Lower Band', line=dict(color='red', dash='dot')))

        signal_df = df[df['Signal'] == 1]
        fig.add_trace(go.Scatter(
            x=signal_df.index,
            y=signal_df['Close'],
            mode='markers+text',
            marker=dict(color='lime', size=10, symbol='triangle-up'),
            text=['Entry']*len(signal_df),
            textposition='top center',
            name='Breakout Entry'))

        fig.update_layout(xaxis_rangeslider_visible=False, height=650)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Signal Log")
        if signal_df.empty:
            st.info("No breakout signals found with current IV setting.")
        else:
            st.dataframe(signal_df[['Open', 'High', 'Low', 'Close', 'Volume']])
            st.download_button(
                label="💾 Download Signal Log",
                data=signal_df.to_csv().encode(),
                file_name="doctor_algo_bot_signals.csv",
                mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error: {e}")
