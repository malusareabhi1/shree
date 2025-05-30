import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Live Supertrend + Pivot + 200 EMA Strategy", layout="wide")
st.title("📈 Live Supertrend + Pivot + 200 EMA Strategy")

# --- Sidebar Inputs ---
symbol = st.sidebar.text_input("Enter Stock Symbol (e.g. TCS.NS for NSE)", value="TCS.NS")
interval = st.sidebar.selectbox("Select Interval", options=["1m", "5m", "15m", "30m", "60m"], index=1)
period = st.sidebar.selectbox("Select Period", options=["1d", "5d", "7d", "30d"], index=1)

stop_loss_pct = st.sidebar.number_input("Stop Loss %", min_value=0.1, max_value=20.0, value=1.0, step=0.1)
target_profit_pct = st.sidebar.number_input("Target Profit %", min_value=0.1, max_value=50.0, value=2.0, step=0.1)

@st.cache_data(show_spinner=True)
def fetch_live_data(symbol, period, interval):
    # Fetch live intraday data from Yahoo Finance
    df = yf.download(tickers=symbol, period=period, interval=interval)
    if df.empty:
        st.error("No data fetched for the symbol/period/interval combination.")
        st.stop()
    df.reset_index(inplace=True)
    df.rename(columns={'Datetime':'Datetime', 'Date':'Datetime'}, inplace=True)  # yfinance sometimes uses Date or Datetime
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=True)
    return df

# Reuse your existing indicator calculation and backtest functions here (with slight adjustments for df index)

@st.cache_data
def calculate_indicators(df):
    required_cols = ['High', 'Low', 'Close']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns in the CSV file. Expected: High, Low, Close.")
        st.stop()

    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # ATR Calculation
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(10).mean()

    # Drop rows with NaN in ATR and other critical columns before calculating bands
    df = df.dropna(subset=['ATR', 'High', 'Low', 'Close']).reset_index(drop=True).copy()

    hl2 = (df['High'] + df['Low']) / 2
    multiplier = 3
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])
    df['in_uptrend'] = True

    col_in_uptrend = df.columns.get_loc('in_uptrend')
    col_lowerband = df.columns.get_loc('LowerBand')
    col_upperband = df.columns.get_loc('UpperBand')

    for current in range(1, len(df)):
        previous = current - 1

        try:
            if df['Close'].iat[current] > df['UpperBand'].iat[previous]:
                df.iat[current, col_in_uptrend] = True
            elif df['Close'].iat[current] < df['LowerBand'].iat[previous]:
                df.iat[current, col_in_uptrend] = False
            else:
                df.iat[current, col_in_uptrend] = df.iat[previous, col_in_uptrend]

                if df.iat[current, col_in_uptrend] and df['LowerBand'].iat[current] < df['LowerBand'].iat[previous]:
                    df.iat[current, col_lowerband] = df['LowerBand'].iat[previous]

                if not df.iat[current, col_in_uptrend] and df['UpperBand'].iat[current] > df['UpperBand'].iat[previous]:
                    df.iat[current, col_upperband] = df['UpperBand'].iat[previous]
        except Exception as e:
            st.error(f"Error at index {current}: {e}")
            break

    return df

# Use your existing run_backtest and plot functions from your code here (unchanged)...

# -- Main Execution --
if symbol:
    df = fetch_live_data(symbol, period, interval)
    st.subheader(f"Showing data for {symbol} ({interval} interval)")

    st.dataframe(df.tail(10))  # show recent 10 candles

    df = calculate_indicators(df)
    trades = run_backtest(df, stop_loss_pct, target_profit_pct)

    st.plotly_chart(plot_chart(df, trades), use_container_width=True)

    if trades:
        st.subheader("📋 Trade Log")
        trades_df = pd.DataFrame(trades)
        st.dataframe(trades_df)

        total_pnl = trades_df.loc[trades_df['Type'] == 'Sell', 'PnL'].sum()
        win_trades = trades_df[(trades_df['Type'] == 'Sell') & (trades_df['PnL'] > 0)]
        win_rate = len(win_trades) / len(trades_df[trades_df['Type'] == 'Sell']) * 100 if len(trades_df[trades_df['Type'] == 'Sell']) > 0 else 0
        avg_pnl = trades_df.loc[trades_df['Type'] == 'Sell', 'PnL'].mean()

        st.metric(label="Total Profit/Loss", value=f"{total_pnl:.2f}")
        st.metric(label="Win Rate (%)", value=f"{win_rate:.2f}")
        st.metric(label="Average PnL per Trade", value=f"{avg_pnl:.2f}")

        st.plotly_chart(plot_equity_curve(trades), use_container_width=True)
    else:
        st.info("No trades generated for the live data.")
else:
    st.info("Please enter a valid stock symbol.")
