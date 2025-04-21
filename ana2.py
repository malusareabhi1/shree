import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Define the stock symbol and timeframe
symbol = 'DIS'
end_date = datetime.today()
start_date = end_date - timedelta(days=120)  # 4 months before today

# Fetch stock data using yfinance
stock_data = yf.download(symbol, start=start_date, end=end_date)

# Calculate technical indicators using pandas-ta
stock_data.ta.macd(append=True)
stock_data.ta.rsi(append=True)
stock_data.ta.bbands(append=True)
stock_data.ta.obv(append=True)

# Calculate additional technical indicators
stock_data.ta.sma(length=20, append=True)
stock_data.ta.ema(length=50, append=True)
stock_data.ta.stoch(append=True)
stock_data.ta.adx(append=True)

# Calculate other indicators
stock_data.ta.willr(append=True)
stock_data.ta.cmf(append=True)
stock_data.ta.psar(append=True)

#convert OBV to million
stock_data['OBV_in_million'] =  stock_data['OBV']/1e7
stock_data['MACD_histogram_12_26_9'] =  stock_data['MACDh_12_26_9'] # not to confuse chatGTP

# Summarize technical indicators for the last day
last_day_summary = stock_data.iloc[-1][['Adj Close',
    'MACD_12_26_9','MACD_histogram_12_26_9', 'RSI_14', 'BBL_5_2.0', 'BBM_5_2.0', 'BBU_5_2.0','SMA_20', 'EMA_50','OBV_in_million', 'STOCHk_14_3_3', 
    'STOCHd_14_3_3', 'ADX_14',  'WILLR_14', 'CMF_20', 
    'PSARl_0.02_0.2', 'PSARs_0.02_0.2'
]]

print("Summary of Technical Indicators for the Last Day:")
print(last_day_summary)
