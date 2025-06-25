import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY 15-Min Chart", layout="wide")
st.title("📈 NIFTY 15-Min Chart – Last 60 Days")

with st.spinner("Fetching NIFTY 15-min data..."):
    ticker = "^NSEI"
    df = yf.download(ticker, interval="15m", period="60d", progress=False)
    df.columns = df.columns.get_level_values(-0)

    # Reset index to move Datetime from index to column
    df.reset_index(inplace=True)

    # Get actual datetime column name after reset
    datetime_col = df.columns[0]

    # Convert to datetime and then IST
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df[datetime_col] = df[datetime_col].dt.tz_convert('Asia/Kolkata')

    # Rename to 'datetime' for consistency
   # Rename column
    df = df.rename(columns={datetime_col: 'datetime'})
    
    # Remove off-market hours (before 9:15 AM or after 3:30 PM IST)
    df = df[(df['datetime'].dt.time >= pd.to_datetime("09:15").time()) &
            (df['datetime'].dt.time <= pd.to_datetime("15:30").time())]
    # Filter 3:00 PM candles
    df_3pm = df[df['datetime'].dt.time == pd.to_datetime("15:00").time()]


# After loading and processing dataframe df
# Assuming you already have the DataFrame `df`
df.columns = df.columns.str.lower()
# Keep only the last 10 **trading days**
df['date'] = df['datetime'].dt.date
last_10_trading_days = sorted(df['date'].unique())[-10:]
df = df[df['date'].isin(last_10_trading_days)]
df = df.drop(columns='date')  # Optional cleanup
# Debug columns
#st.write("Columns available:", df.columns.tolist())

# Check columns exist
required_cols = ['datetime', 'open', 'high', 'low', 'close']
if not all(col in df.columns for col in required_cols):
    missing = [col for col in required_cols if col not in df.columns]
    st.error(f"Missing columns: {missing}")
    st.stop()


# Show dataframe sample
st.dataframe(df.head())

# Then proceed to plot
fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name='NIFTY'
)])
st.plotly_chart(fig)


# Preview data
#st.subheader("📋 Data Preview")
#st.dataframe(df.tail(50))

# Candlestick chart
st.subheader("🕯️ NIFTY Candlestick Chart (15m)")

fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="NIFTY"
)])

fig.update_traces(increasing_line_color='green', decreasing_line_color='red')

fig.update_layout(
    title="NIFTY 15-Min Chart (Last 10 Trading Days)",
    xaxis_title="DateTime (IST)",
    yaxis_title="Price",
    xaxis_rangeslider_visible=False,
    xaxis=dict(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),
            dict(bounds=[16, 9.15], pattern="hour")
        ],
        showgrid=False
    ),
    yaxis=dict(showgrid=True),
    plot_bgcolor='black',
    paper_bgcolor='black',
    font=dict(color='white'),
    height=600
)

st.plotly_chart(fig, use_container_width=True)
