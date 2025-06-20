import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.title("📊 NIFTY 3PM Candle Breakout Tracker")

# User parameters
points_required = 100
symbol = "^NSEI"  # NIFTY 50 index
interval = "15m"
days_to_check = 100

st.write(f"Fetching NIFTY {interval} data for the last {days_to_check} trading days...")

# Load past 30 days of data with 15m interval (~390 candles/day, so 30 days gives approx 100 trading days)
data = yf.download(symbol, period="30d", interval=interval)
data.dropna(inplace=True)

# Prepare day-wise split
data['Date'] = data.index.date
data['Time'] = data.index.time

# Identify 15-min 3:00 PM candles
three_pm_time = datetime.strptime("15:00:00", "%H:%M:%S").time()
three_pm_close = data[data['Time'] == three_pm_time][['Close']]
three_pm_close = three_pm_close.rename(columns={'Close': '3PM_Close'})
three_pm_close['Date'] = three_pm_close.index.date

# Shift date to match next day
three_pm_close['NextDate'] = three_pm_close['Date'].shift(-1)

# Final scan
result = []
unique_dates = three_pm_close['NextDate'].dropna().unique()

for next_date in unique_dates:
    try:
        # 3PM close from previous day
        prev_close = three_pm_close[three_pm_close['NextDate'] == next_date]['3PM_Close'].values[0]
        # Next day full data
        next_day_data = data[data['Date'] == next_date]

        crossed = False
        crossed_time = None
        high_after_cross = None

        for i in range(1, len(next_day_data)):
            prev = next_day_data.iloc[i - 1]
            curr = next_day_data.iloc[i]
            # Check cross from below
            if prev['Close'] < prev_close and curr['Close'] > prev_close:
                crossed = True
                crossed_time = curr.name
                high_after_cross = next_day_data.iloc[i:]['High'].max()
                break

        if crossed and high_after_cross and high_after_cross >= (prev_close + points_required):
            result.append({
                "Date": next_date,
                "Prev 3PM Close": prev_close,
                "Crossed Time": crossed_time,
                "High After Cross": high_after_cross
            })

    except Exception as e:
        st.warning(f"Error on date {next_date}: {e}")
        continue

# Output result
st.subheader(f"✅ Total Matches: {len(result)}")
if result:
    df_result = pd.DataFrame(result)
    st.dataframe(df_result)
else:
    st.info("No matching scenario found in last 100 trading days.")

