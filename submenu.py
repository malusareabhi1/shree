import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def check_swing_trade_pullback(stock_symbol='TCS.NS', days=90):
    print(f"\n🔍 Checking swing trade (pullback) for: {stock_symbol}")

    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')

    # ✅ Basic data validation
    if df.empty or 'Close' not in df.columns or df['Close'].isnull().all():
        print("❌ Data unavailable or 'Close' prices missing.")
        return

    # ✅ Calculate EMA20 only if 'Close' exists and is valid
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()

    if 'EMA20' not in df.columns or df['EMA20'].isnull().all():
        print("❌ EMA20 could not be calculated.")
        return

    # ✅ Drop rows where EMA20 is NaN
    df = df.dropna(subset=['EMA20'])

    # ✅ Bullish Engulfing Pattern
    df['Bullish_Engulfing'] = (
        (df['Close'].shift(1) < df['Open'].shift(1)) &  # previous red
        (df['Close'] > df['Open']) &                   # current green
        (df['Close'] > df['Open'].shift(1)) &          # current close > prev open
        (df['Open'] < df['Close'].shift(1))            # current open < prev close
    )

    # ✅ Trend check (price > EMA)
    df['Trend'] = df['Close'] > df['EMA20']

    # ✅ Signal if both are True
    df['SwingSignal'] = df['Bullish_Engulfing'] & df['Trend']

    recent = df.tail(10)
    signals = recent[recent['SwingSignal']]

    if not signals.empty:
        print(f"\n📈 Swing BUY signal(s) for {stock_symbol}:")
        print(signals[['Close', 'EMA20', 'Bullish_Engulfing', 'Trend']])
    else:
        print("❌ No swing signal found in last 10 days.")

    # ✅ Optional plot
    try:
        df.tail(60)[['Close', 'EMA20']].plot(figsize=(10, 4), title=f"{stock_symbol} - Pullback Swing Setup")
        plt.grid(True)
        plt.show()
    except Exception as e:
        print(f"⚠️ Plotting error: {e}")

# Example usage
check_swing_trade_pullback("TCS.NS")
