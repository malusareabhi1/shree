import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def check_swing_trade_pullback(stock_symbol='TCS.NS', days=60):
    print(f"\n🔍 Checking swing trade (pullback) for: {stock_symbol}")

    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')

    if df.empty or 'Close' not in df.columns:
        print("❌ Data unavailable or missing.")
        return

    df['EMA20'] = df['Close'].ewm(span=20).mean()

    # Bullish Engulfing condition
    df['Bullish_Engulfing'] = (
        (df['Close'].shift(1) < df['Open'].shift(1)) &  # previous red
        (df['Close'] > df['Open']) &                   # current green
        (df['Close'] > df['Open'].shift(1)) &          # current close > prev open
        (df['Open'] < df['Close'].shift(1))            # current open < prev close
    )

    # Uptrend condition
    df['Trend'] = df['Close'] > df['EMA20']

    # Final signal
    df['SwingSignal'] = df['Bullish_Engulfing'] & df['Trend']

    recent = df.tail(10)
    signals = recent[recent['SwingSignal']]

    if not signals.empty:
        print(f"\n📈 Swing BUY signal(s) found for {stock_symbol}:")
        print(signals[['Close', 'EMA20', 'Bullish_Engulfing']])
    else:
        print("❌ No swing signal found in last 10 days.")

    # Optional plot
    try:
        df.tail(60)[['Close', 'EMA20']].plot(figsize=(10, 4), title=f"{stock_symbol} - Pullback Swing Setup")
        plt.grid(True)
        plt.show()
    except Exception as e:
        print(f"⚠️ Plot error: {e}")

# Example
check_swing_trade_pullback("TCS.NS")
