import yfinance as yf
import pandas_ta as ta

data = yf.download("AAPL", start="2023-01-01", end="2023-05-01", interval="1d")

# Add candlestick pattern detection, e.g. hammer
data['hammer'] = ta.cdl_pattern(data['Open'], data['High'], data['Low'], data['Close']).hammer

print(data[data['hammer'] != 0])
