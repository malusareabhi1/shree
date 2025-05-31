import yfinance as yf
import pandas as pd
import ta
import time

def get_rsi_signal(symbol="RELIANCE.NS", interval="5m", lookback="1d", rsi_period=14):
    try:
        df = yf.download(tickers=symbol, interval=interval, period=lookback, progress=False)

        if df.empty or 'Close' not in df.columns:
            print(f"No data fetched for {symbol}.")
            return

        df.dropna(inplace=True)  # Remove any rows with NaN

        # Calculate RSI
        rsi_calc = ta.momentum.RSIIndicator(close=df['Close'], window=rsi_period)
        df['RSI'] = rsi_calc.rsi()

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

    except Exception as e:
        print(f"Error fetching or processing data: {e}")

# Run once or in a loop
if __name__ == "__main__":
    symbol = "RELIANCE.NS"
    while True:
        get_rsi_signal(symbol)
        time.sleep(300)  # 5-minute interval
