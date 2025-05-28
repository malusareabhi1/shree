import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def check_swing_trade(stock_symbol='TCS.NS', days=90):
    print(f"\n🔍 Checking swing trade for: {stock_symbol}")

    # Step 1: Download data
    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')

    if df.empty:
        print(f"❌ Failed to download data for {stock_symbol}.")
        return

    # Step 2: Confirm 'Close' exists
    if 'Close' not in df.columns:
        print(f"❌ 'Close' column not found for {stock_symbol}. Data columns: {df.columns.tolist()}")
        return

    # Step 3: Calculate EMA44
    df['EMA44'] = df['Close'].ewm(span=44).mean()

    # Step 4: Drop NaNs only after confirming 'EMA44' exists
    if 'EMA44' not in df.columns or df['EMA44'].isna().all():
        print(f"❌ EMA44 not calculated properly for {stock_symbol}.")
        return

    df = df.dropna(subset=['EMA44'])

    # Step 5: Signal & Crossover
    df['Signal'] = df['Close'] > df['EMA44']
    df['Crossover'] = df['Signal'] & (~df['Signal'].shift(1))

    # Step 6: Check last 10 candles
    recent = df.tail(10)

    if 'Crossover' not in recent.columns:
        print(f"❌ 'Crossover' column missing in recent data.")
        return

    signals = recent[recent['Crossover']]

    # Step 7: Output
    if not signals.empty:
        print(f"\n📈 Swing Buy Signal Detected in {stock_symbol} on:")
        print(signals[['Close', 'EMA44']])
    else:
        print(f"\n❌ No Swing Signal Found in {stock_symbol} (last 10 days).")

    # Step 8: Plot (optional, comment out in headless servers)
    try:
        recent[['Close', 'EMA44']].plot(title=f"{stock_symbol} Price vs EMA44")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.grid()
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"⚠️ Plotting failed: {e}")

# Run test
check_swing_trade('TCS.NS')
