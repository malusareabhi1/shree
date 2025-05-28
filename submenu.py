import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def check_swing_trade(stock_symbol='TCS.NS', days=90):
    print(f"\n🔍 Checking swing trade for: {stock_symbol}")

    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')

    if df.empty:
        print(f"❌ No data found for {stock_symbol}")
        return

    if 'Close' not in df.columns:
        print(f"❌ 'Close' column missing in downloaded data.")
        return

    # Calculate EMA only if data is long enough
    if len(df) < 44:
        print(f"❌ Not enough data to compute EMA44. Rows: {len(df)}")
        return

    df['EMA44'] = df['Close'].ewm(span=44).mean()

    # Ensure 'EMA44' has valid values
    if 'EMA44' not in df.columns or df['EMA44'].isnull().all():
        print("❌ EMA44 column missing or contains only NaNs.")
        return

    # Drop rows with NaN EMA
    df = df.dropna(subset=['EMA44'])

    df['Signal'] = df['Close'] > df['EMA44']
    df['Crossover'] = df['Signal'] & (~df['Signal'].shift(1))

    recent = df.tail(10)
    if 'Crossover' not in recent.columns:
        print("❌ 'Crossover' column missing.")
        return

    signals = recent[recent['Crossover']]

    if not signals.empty:
        print(f"\n📈 Swing BUY signal found in {stock_symbol} on:")
        print(signals[['Close', 'EMA44']])
    else:
        print(f"\n❌ No swing signal in last 10 candles of {stock_symbol}")

    # Optional plot
    try:
        recent[['Close', 'EMA44']].plot(title=f"{stock_symbol} Price vs EMA44")
        plt.grid()
        plt.show()
    except Exception as e:
        print(f"⚠️ Plotting error: {e}")

# ✅ Test
check_swing_trade('TCS.NS')
