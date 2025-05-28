import yfinance as yf
import talib

# Download stock data
data = yf.download("AAPL", start="2023-01-01", end="2023-05-01", interval="1d")

# TA-Lib requires numpy arrays
open = data['Open'].values
high = data['High'].values
low = data['Low'].values
close = data['Close'].values

# Detect Hammer candlestick pattern (example)
hammer = talib.CDLHAMMER(open, high, low, close)

data['Hammer'] = hammer

print(data[data['Hammer'] != 0][['Open', 'High', 'Low', 'Close', 'Hammer']])

