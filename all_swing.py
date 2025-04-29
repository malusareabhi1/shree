import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

from datetime import datetime

# --- Helper functions for each strategy ---
def moving_average_crossover(data):
    data = data.copy()
    data['SMA_9'] = data['Close'].rolling(window=9).mean()
    data['SMA_21'] = data['Close'].rolling(window=21).mean()
    data['Signal'] = 0
    data.loc[data['SMA_9'] > data['SMA_21'], 'Signal'] = 1
    data.loc[data['SMA_9'] < data['SMA_21'], 'Signal'] = -1
    data.dropna(inplace=True)
    return data

def breakout_strategy(data):
    data = data.copy()
    
    # Calculate High and Low rolling windows
    data['High_20'] = data['High'].rolling(window=20).max()
    data['Low_20'] = data['Low'].rolling(window=20).min()
    
    # Shift the high/low values by 1 for comparison
    high_shifted = data['High_20'].shift(1)
    low_shifted = data['Low_20'].shift(1)

    # Initialize 'Signal' column
    data['Signal'] = 0
    
    # Mask for long (buy) signals where Close > shifted High_20
    mask_long = (data['Close'] > high_shifted) & high_shifted.notna()
    
    # Mask for short (sell) signals where Close < shifted Low_20
    mask_short = (data['Close'] < low_shifted) & low_shifted.notna()
    
    # Apply the signals
    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    
    # Drop NaN values that may appear during the rolling window calculations
    data.dropna(subset=['Signal'], inplace=True)
    
    return data


def fibonacci_pullback(data):
    data = data.copy()
    data['Signal'] = 0
    for i in range(20, len(data)):
        high = data['High'][i-20:i].max()
        low = data['Low'][i-20:i].min()
        diff = high - low
        fib_61 = high - 0.618 * diff
        fib_50 = high - 0.5 * diff
        fib_38 = high - 0.382 * diff
        close = data['Close'].iloc[i]
        if np.isclose(close, [fib_38, fib_50, fib_61], atol=0.01).any():
            data.loc[data.index[i], 'Signal'] = 1
    data.dropna(inplace=True)
    return data

def rsi_strategy(data):
    data = data.copy()
    delta = data['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Signal'] = 0
    data.loc[data['RSI'] < 30, 'Signal'] = 1
    data.loc[data['RSI'] > 70, 'Signal'] = -1
    data.dropna(inplace=True)
    return data

def volume_price_action(data):
    data = data.copy()
    data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
    data['Signal'] = 0
    mask = (data['Volume'] > data['Volume_SMA']) & (data['Close'] > data['Open'])
    data.loc[mask, 'Signal'] = 1
    data.dropna(inplace=True)
    return data

def ichimoku_cloud(data):
    data = data.copy()
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    data['Signal'] = 0
    mask_long = (tenkan_sen > kijun_sen) & tenkan_sen.notna() & kijun_sen.notna()
    mask_short = (tenkan_sen < kijun_sen) & tenkan_sen.notna() & kijun_sen.notna()

    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    data.dropna(inplace=True)
    return data

def macd_strategy(data):
    data = data.copy()
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    data['Signal'] = 0
    mask_long = (macd > signal_line) & macd.notna() & signal_line.notna()
    mask_short = (macd < signal_line) & macd.notna() & signal_line.notna()
    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    data.dropna(inplace=True)
    return data

# --- Backtest function ---
def backtest(data):
    data = data.copy()
    data['Returns'] = data['Close'].pct_change()
    data['Strategy'] = data['Signal'].shift(1) * data['Returns']
    data.dropna(inplace=True)
    return data['Strategy'].cumsum()

# --- Streamlit UI ---
st.title("🧠 Compare Swing Trading Strategies")
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, NIFTY)", "AAPL")
start_date = st.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.date_input("End Date", datetime.today())

strategies = {
    'MA Crossover': moving_average_crossover,
    'Breakout': breakout_strategy,
    'Fibonacci Pullback': fibonacci_pullback,
    'RSI Strategy': rsi_strategy,
    'Volume + Price Action': volume_price_action,
    'Ichimoku': ichimoku_cloud,
    'MACD': macd_strategy
}

strategy_name = st.sidebar.selectbox("Select Strategy", list(strategies.keys()))
selected_strategy = strategies[strategy_name]

if st.sidebar.button("Run Backtest"):
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error("No data found for the ticker.")
    else:
        # Column requirements
        required_cols = ['Close']

        if strategy_name in ['Breakout', 'Fibonacci Pullback', 'Ichimoku']:
            required_cols += ['High', 'Low']
        if strategy_name == 'Volume + Price Action':
            required_cols += ['Open', 'Volume']

        if not all(col in data.columns for col in required_cols):
            st.error(f"The selected strategy '{strategy_name}' requires columns {required_cols} but missing in data.")
        else:
            df = selected_strategy(data.copy())
            pnl = backtest(df)

            st.subheader(f"Cumulative Returns: {strategy_name}")
            plt.figure(figsize=(10, 6))
            plt.plot(pnl, label=strategy_name)
            plt.title(f"{strategy_name} Strategy Performance on {ticker}")
            plt.xlabel("Date")
            plt.ylabel("Cumulative Return")
            plt.legend()
            st.pyplot(plt.gcf())
            plt.clf()
