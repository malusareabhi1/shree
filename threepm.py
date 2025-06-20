import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY 15-Min Candlestick", layout="wide")

st.title("📈 NIFTY 15-Minute Candlestick Chart (Last 60 Days) - Market Hours Only")

# Download data
data = yf.download("^NSEI", period="60d", interval="15m", progress=False)

# Flatten MultiIndex columns if any
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

data.dropna(inplace=True)

# Convert timezone from UTC to IST
if data.index.tz is None:
    data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
else:
    data.index = data.index.tz_convert('Asia/Kolkata')

# After converting index to IST and resetting index:

data.reset_index(inplace=True)

# Filter to market hours (09:15 to 15:30 IST)
market_open = pd.to_datetime("09:15:00").time()
market_close = pd.to_datetime("15:30:00").time()

data = data[(data['Datetime'].dt.time >= market_open) & (data['Datetime'].dt.time <= market_close)]

# Reset index to get Datetime as a column
data.reset_index(inplace=True)

# Filter to market days (Monday=0, Sunday=6)
data['Weekday'] = data['Datetime'].dt.weekday
data = data[data['Weekday'] < 5]  # Keep Mon-Fri only

# Filter to market hours: 09:15 to 15:30 IST
data['Time'] = data['Datetime'].dt.time
start_time = pd.to_datetime("09:15:00").time()
end_time = pd.to_datetime("15:30:00").time()

data = data[(data['Time'] >= start_time) & (data['Time'] <= end_time)]

# Drop helper columns
data.drop(columns=['Weekday', 'Time'], inplace=True)

# Select relevant columns
data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Plot entire filtered data
st.subheader("📊 NIFTY 15-Min Candlestick Chart (Market Hours Only)")

fig = go.Figure(data=[go.Candlestick(
    x=data['Datetime'],
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name="NIFTY"
)])

fig.update_layout(
    xaxis_title='Time (IST)',
    yaxis_title='Price',
    xaxis_rangeslider_visible=False,
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# Optional: Show raw data
with st.expander("🔍 Show raw data"):
    st.dataframe(data)
