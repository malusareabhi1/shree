import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def check_swing_trade(stock_symbol='TCS.NS', days=90):
    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')

    # Check if data was downloaded
    if df.empty:
        print(f"❌ Failed to download data for {stock_symbol}.")
        return

    # Check required column
    if 'Close' not in df.columns:
        print(f"❌ 'Close' column missing for {stock_symbol}.")
        return

    # Calculate EMA
    df['EMA44'] = df['Close'].ewm(span=44).mean()

    # Drop rows where EMA44 is NaN
    if 'EMA44' not in df.columns:
        print(f"❌ EMA44 not computed for {stock_symbol}.")
        return

    df = df.dropna(subset=['EMA44'])

    # Signal and Crossover Logic
    df['Signal'] = df['Close'] > df['EMA44']
    df['Crossover'] = df['Signal'] & (~df['Signal'].shift(1))

    recent = df.tail(10)
    signals = recent[recent['Crossover']]

    if not signals.empty:
        print(f"\n📈 Swing Buy Setup Detected in {stock_symbol} on:")
        print(signals[['Close', 'EMA44']])
    else:
        print(f"\n❌ No Swing Trade Signal Found in {stock_symbol} (last 10 days).")

    # Plot
    recent[['Close', 'EMA44']].plot(title=f"{stock_symbol} Price & EMA44")
    plt.show()

# Example
check_swing_trade('TCS.NS')
