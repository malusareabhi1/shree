import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from datetime import datetime

# 1. Configuration
symbol = "HDFCBANK.NS"  # You can change this to any NIFTY 100 stock
start_date = "2021-01-01"
end_date = datetime.today().strftime('%Y-%m-%d')

# 2. Fetch data
df = yf.download(symbol, start=start_date, end=end_date)
df.dropna(inplace=True)

# 3. Indicators
df['20EMA'] = EMAIndicator(df['Close'], window=20).ema_indicator()
df['200EMA'] = EMAIndicator(df['Close'], window=200).ema_indicator()
df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()
df['VolumeAvg20'] = df['Volume'].rolling(20).mean()

# 4. Signal Conditions
df['Signal'] = (
    (df['Close'] > df['200EMA']) &
    (df['Close'] > df['20EMA']) &
    (df['RSI'] >= 45) & (df['RSI'] <= 60) &
    (df['Close'] > df['High'].shift(1)) &
    (df['Volume'] > 1.5 * df['VolumeAvg20'])
)

# 5. Entry/Exit Logic
entries = []
exits = []
for i in range(1, len(df)-1):
    if df.iloc[i]['Signal']:
        entry_price = df.iloc[i+1]['Open']
        sl = df.iloc[i-3:i]['Low'].min()  # Recent swing low
        target1 = entry_price + (entry_price - sl) * 2
        target2 = entry_price + (entry_price - sl) * 3
        for j in range(i+1, len(df)):
            high = df.iloc[j]['High']
            low = df.iloc[j]['Low']
            close = df.iloc[j]['Close']
            if low < sl:
                exits.append({'EntryDate': df.index[i+1], 'ExitDate': df.index[j], 'Entry': entry_price, 'Exit': sl, 'Result': 'SL'})
                break
            elif high > target2:
                exits.append({'EntryDate': df.index[i+1], 'ExitDate': df.index[j], 'Entry': entry_price, 'Exit': target2, 'Result': 'Target2'})
                break
            elif high > target1:
                exits.append({'EntryDate': df.index[i+1], 'ExitDate': df.index[j], 'Entry': entry_price, 'Exit': target1, 'Result': 'Target1'})
                break

# 6. Results
results_df = pd.DataFrame(exits)
results_df['PnL'] = results_df['Exit'] - results_df['Entry']
results_df['Return%'] = (results_df['PnL'] / results_df['Entry']) * 100

print("\nBacktest Summary:")
print(results_df['Result'].value_counts())
print(f"Total Trades: {len(results_df)}")
print(f"Win Rate: {round(len(results_df[results_df['PnL'] > 0]) / len(results_df) * 100, 2)}%")
print(f"Avg Return per Trade: {results_df['Return%'].mean():.2f}%")

# 7. Equity Curve
results_df['Equity'] = results_df['PnL'].cumsum()
plt.figure(figsize=(10, 5))
plt.plot(results_df['ExitDate'], results_df['Equity'], label='Equity Curve')
plt.title(f"{symbol} - Momentum Pullback Swing Strategy")
plt.xlabel("Date")
plt.ylabel("Cumulative PnL")
plt.grid()
plt.legend()
plt.tight_layout()
plt.show()
