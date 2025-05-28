import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def check_swing_trade(stock_symbol='TCS.NS', days=90):
    print(f"\n🔍 Checking swing trade for: {stock_symbol}")

    # Step 1: Download data
    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')

    if df.empty:
        print(f"❌ No data found for {stock_symbol}")
        return

    if 'Close' not in df.columns:
        print(f"❌ 'Close' column missing in downloaded data.")
        return

    if len(df) < 50:
        print(f"❌ Not enough data to compute EMA44. Available: {len(df)} rows")
        return

    # Step 2: Calculate EMA44
    df['EMA44'] = df['Close'].ewm(span=44).mean()

    # Step 3: Ensure EMA44 was created
    if 'EMA44' not in df.columns:
        print("❌ EMA44 calculation failed.")
        return

    # Step 4: Drop rows where EMA44 is NaN
    if df['EMA44'].isnull().all():
        print("❌ All EMA44 values are NaN.")
        return

    df = df.dropna(subset=['EMA44'])

    # Step 5: Signal logic
    df['Signal'] = df['Close'] > df['EMA44']
    df['Crossover'] = df['Signal'] & (~df['Signal'].shift(1))

    recent = df.tail(10)
    signals = recent[recent['Crossover']]

    if not signals.empty:
        print(f"\n📈 Swing BUY signal found in {stock_symbol} on:")
        print(signals[['Close', 'EMA44']])
    else:
        print(f"\n❌ No swing signal in last 10 candles of {stock_symbol}")

    # Step 6: Optional Plot
    try:
        recent[['Close', 'EMA44']].plot(title=f"{stock_symbol} Price vs EMA44", figsize=(10,4))
        plt.grid(True)
        plt.show()
    except Exception as e:
        print(f"⚠️ Plotting error: {e}")

# ✅ Run the check
check_swing_trade('TCS.NS')
