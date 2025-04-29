import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

from datetime import datetime

# --- Helper functions for each strategy ---
def moving_average_crossover(data):
    data['SMA_9'] = data['Close'].rolling(window=9).mean()
    data['SMA_21'] = data['Close'].rolling(window=21).mean()
    data['Signal'] = 0
    data.loc[data['SMA_9'] > data['SMA_21'], 'Signal'] = 1
    data.loc[data['SMA_9'] < data['SMA_21'], 'Signal'] = -1
    return data

def breakout_strategy(data):
    data['High_20'] = data['High'].rolling(window=20).max()
    data['Low_20'] = data['Low'].rolling(window=20).min()
    data['Signal'] = 0
    mask_long = (data['Close'] > data['High_20'].shift(1)) & (data['High_20'].shift(1).notna())
    mask_short = (data['Close'] < data['Low_20'].shift(1)) & (data['Low_20'].shift(1).notna())
    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    return data

def fibonacci_pullback(data):
    data['Signal'] = 0
    for i in range(20, len(data)):
        high = data['High'][i-20:i].max()
        low = data['Low'][i-20:i].min()
        diff = high - low
        fib_61 = high - 0.618 * diff
        fib_50 = high - 0.5 * diff
        fib_38 = high - 0.382 * diff
        if data['Close'][i] in [fib_38, fib_50, fib_61]:
            data.loc[data.index[i], 'Signal'] = 1
    return data

def rsi_strategy(data):
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
    return data

def volume_price_action(data):
    data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
    data['Signal'] = 0
    signal = (data['Volume'] > data['Volume_SMA']) & (data['Close'] > data['Open'])
    data.loc[signal, 'Signal'] = 1
    return data

def ichimoku_cloud(data):
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    data['Signal'] = 0
    data.loc[tenkan_sen > kijun_sen, 'Signal'] = 1
    data.loc[tenkan_sen < kijun_sen, 'Signal'] = -1
    return data

def macd_strategy(data):
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    data['Signal'] = 0
    data.loc[macd > signal_line, 'Signal'] = 1
    data.loc[macd < signal_line, 'Signal'] = -1
    return data

# --- Backtest function ---
def backtest(data):
    data['Returns'] = data['Close'].pct_change()
    data['Strategy'] = data['Signal'].shift(1) * data['Returns']
    return data['Strategy'].cumsum()

# --- Streamlit UI ---
st.title("Compare Swing Trading Strategies")
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, NIFTY)", "AAPL")
start_date = st.date_input("Start Date", datetime(2020, 1, 1))
end_date = st.date_input("End Date", datetime.today())

if st.button("Run Backtest"):
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        st.error("No data found.")
    else:
        strategies = {
            'MA Crossover': moving_average_crossover,
            'Breakout': breakout_strategy,
            'Fibonacci Pullback': fibonacci_pullback,
            'RSI Strategy': rsi_strategy,
            'Volume + Price Action': volume_price_action,
            'Ichimoku': ichimoku_cloud,
            'MACD': macd_strategy
        }

        results = {}
        for name, func in strategies.items():
            df = data.copy()
            df = func(df)
            pnl = backtest(df)
            results[name] = pnl

        # Plotting results
        for name, pnl in results.items():
            plt.plot(pnl, label=name)
        plt.title("Cumulative Returns of Swing Strategies")
        plt.legend()
        st.pyplot(plt.gcf())
        plt.clf()
