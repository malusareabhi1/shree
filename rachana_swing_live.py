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
    # Flatten multi-index columns if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns]
        
    df.reset_index(inplace=True)
    df.rename(columns={'Datetime':'Datetime', 'Date':'Datetime'}, inplace=True)  # yfinance sometimes uses Date or Datetime
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=True)
    return df

# Reuse your existing indicator calculation and backtest functions here (with slight adjustments for df index)

@st.cache_data
@st.cache_data
def calculate_indicators(df):
    # Step 1: Basic column validation
    required_cols = ['High', 'Low', 'Close']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns: High, Low, Close.")
        st.stop()

    df = df.copy()  # Safe copy

    # Step 2: Calculate EMA
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # Step 3: Calculate True Range components
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))

    # Step 4: Drop NaNs from TR components
    df.dropna(subset=['H-L', 'H-PC', 'L-PC'], inplace=True)

    # Step 5: Calculate True Range
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)

    # Step 6: ATR using 10-period SMA
    df['ATR'] = df['TR'].rolling(window=10).mean()

    # Step 7: Drop initial NaNs from ATR
    df.dropna(subset=['ATR'], inplace=True)

    # Step 8: Supertrend-like Bands
    hl2 = (df['High'] + df['Low']) / 2
    multiplier = 3
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])

    # Step 9: Initialize trend
    df['in_uptrend'] = True

    # Step 10: Trend logic loop
    for current in range(1, len(df)):
        previous = current - 1

        if df.iloc[current]['Close'] > df.iloc[previous]['UpperBand']:
            df.at[current, 'in_uptrend'] = True
        elif df.iloc[current]['Close'] < df.iloc[previous]['LowerBand']:
            df.at[current, 'in_uptrend'] = False
        else:
            df.at[current, 'in_uptrend'] = df.at[previous, 'in_uptrend']
            if df.at[current, 'in_uptrend']:
                df.at[current, 'LowerBand'] = min(df.at[current, 'LowerBand'], df.at[previous, 'LowerBand'])
            else:
                df.at[current, 'UpperBand'] = max(df.at[current, 'UpperBand'], df.at[previous, 'UpperBand'])

    return df.reset_index(drop=True)



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
