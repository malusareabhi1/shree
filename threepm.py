import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY 15-Min Candlestick", layout="wide")

st.title("📈 NIFTY 15-Minute Candlestick Chart (Last 60 Days)")

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

# Reset index to get Datetime as a column
data.reset_index(inplace=True)

# Select relevant columns
data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Plot entire data in one chart
st.subheader("📊 Candlestick Chart for Last 60 Days (15-min Interval)")

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
