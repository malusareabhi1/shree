import yfinance as yf
import pandas as pd
import streamlit as st
def scan_bhanushali_strategy(stock):
    # Download historical stock data
    df = yf.download(stock, period='90d', interval='1d')

    # Calculate the 44-period SMA
    df['SMA44'] = df['Close'].rolling(window=44).mean()

    # Drop rows with NaN values (if any)
    df.dropna(inplace=True)

    if len(df) < 2:
        return None  # Not enough data

    last_candle = df.iloc[-1]  # Get the most recent candle (row)
    prev_candle = df.iloc[-2]  # Get the previous candle (row)

    # Ensure you're working with scalar values
    low = last_candle['Low']
    close = last_candle['Close']
    sma44 = last_candle['SMA44']

    # Ensure values are scalar (individual numbers)
    if isinstance(low, pd.Series): low = low.values[0]
    if isinstance(close, pd.Series): close = close.values[0]
    if isinstance(sma44, pd.Series): sma44 = sma44.values[0]

    # Condition: low < SMA44 < close (candle near rising 44 SMA)
    if low < sma44 < close:
        # Buy above the high of the candle, stoploss below the low of the candle
        entry = last_candle['High']
        stoploss = low

        # Calculate targets based on a 1:2 and 1:3 risk-reward ratio
        target1 = entry + (entry - stoploss) * 2
        target2 = entry + (entry - stoploss) * 3

        # Return a dictionary with the results
        return {
            'symbol': stock,
            'entry': round(entry, 2),
            'stoploss': round(stoploss, 2),
            'target_1_2': round(target1, 2),
            'target_1_3': round(target2, 2)
        }

    return None

# Example usage with a list of NIFTY 100 stocks
nifty_100 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'KOTAKBANK.NS', 'ITC.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS'
    # Add more stock symbols here...
]

# Scan and collect results
results = []
for stock in nifty_100:
    try:
        res = scan_bhanushali_strategy(stock)
        if res:
            results.append(res)
    except Exception as e:
        st.write(f"Error with {stock}: {e}")

# Print the results
for result in results:
    st.write(result)







