import yfinance as yf
import pandas as pd
import ta
import time

def get_rsi_signal(symbol="RELIANCE.NS", interval="5m", lookback="1d", rsi_period=14):
    # Fetch live data from Yahoo Finance
    df = yf.download(tickers=symbol, interval=interval, period=lookback)
    if df.empty:
        print("No data fetched.")
        return

    # Calculate RSI
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=rsi_period).rsi()

    # Get the latest RSI value
    latest_rsi = df['RSI'].iloc[-1]
    last_price = df['Close'].iloc[-1]

    # Signal logic
    if latest_rsi < 30:
        signal = "BUY"
    elif latest_rsi > 70:
        signal = "SELL"
    else:
        signal = "HOLD"

    print(f"\nSymbol: {symbol}")
    print(f"Last Price: ₹{round(last_price, 2)}")
    print(f"RSI({rsi_period}): {round(latest_rsi, 2)} -> Signal: {signal}")

    return signal, last_price, latest_rsi

# Run continuously every 5 minutes
if __name__ == "__main__":
    symbol = "RELIANCE.NS"
    while True:
        get_rsi_signal(symbol)
        time.sleep(300)  # Wait 5 minutes
