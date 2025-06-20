import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY 15-Min Candlestick", layout="wide")

st.title("📈 NIFTY 15-Minute Candlestick Chart (Last 60 Days)")

# Step 1: Download data
data = yf.download("^NSEI", period="60d", interval="15m", progress=False)

# Step 2: Flatten MultiIndex columns (if any)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

# Step 3: Drop NA
data.dropna(inplace=True)

# Check if index is timezone-aware or not, then do the right thing:
if data.index.tz is None:
    data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
else:
    data.index = data.index.tz_convert('Asia/Kolkata')

# Step 4: Reset index to get Datetime as column
data.reset_index(inplace=True)

# Step 5: Rename columns safely
data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]

# Step 6: Let user pick a specific date to plot (in IST now)
data['Date'] = data['Datetime'].dt.date
unique_dates = sorted(data['Date'].unique(), reverse=True)
selected_date = st.selectbox("📅 Select a Date to Plot:", unique_dates)

# Filter data for selected date
plot_data = data[data['Date'] == selected_date]

# Step 7: Plot candlestick
st.subheader(f"📊 Candlestick Chart for {selected_date} (IST)")
fig = go.Figure(data=[go.Candlestick(
    x=plot_data['Datetime'],
    open=plot_data['Open'],
    high=plot_data['High'],
    low=plot_data['Low'],
    close=plot_data['Close'],
    name="NIFTY"
)])

fig.update_layout(
    xaxis_title='Time (IST)',
    yaxis_title='Price',
    xaxis_rangeslider_visible=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# Optional: show raw data
with st.expander("🔍 Show raw data"):
    st.dataframe(plot_data)
