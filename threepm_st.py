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
    # Convert columns to lowercase now
df.columns = df.columns.str.lower()

    


# After loading and processing dataframe df
# Convert all column names to lowercase
df.columns = df.columns.str.lower()

# Filter to last 10 trading days
df['date'] = df['datetime'].dt.date
last_10_trading_days = sorted(df['date'].unique())[-10:]
df = df[df['date'].isin(last_10_trading_days)]
df = df.drop(columns='date')

# ✅ Now safe to filter 3PM candles (after lowercase and filtering)
df_3pm = df[(df['datetime'].dt.hour == 15) & (df['datetime'].dt.minute == 0)]
###############################################################################################################################
# Trade log: check if next day breaks 3PM high + 50 points
trade_log = []

for i in range(len(df_3pm) - 1):  # Avoid last day, no "next day" after it
    current_row = df_3pm.iloc[i]
    next_row = df_3pm.iloc[i + 1]

    threepm_date = current_row['datetime'].date()
    next_day_date = next_row['datetime'].date()

    threepm_high = current_row['high']
    target = threepm_high + 50

    # Filter next day's data
    next_day_data = df[df['datetime'].dt.date == next_day_date]

    if next_day_data.empty:
        hit = False
        hit_time = None
    else:
        breakout = next_day_data[next_day_data['high'] >= target]
        hit = not breakout.empty
        hit_time = breakout['datetime'].iloc[0] if hit else None

    trade_log.append({
        '3PM Date': threepm_date,
        'Next Day': next_day_date,
        '3PM High': round(threepm_high, 2),
        'Target (High + 50)': round(target, 2),
        'Hit?': '✅ Yes' if hit else '❌ No',
        'Hit Time': hit_time.time() if hit else '-'
    })

# Convert to DataFrame
trade_log_df = pd.DataFrame(trade_log)

####################################################################################################################################
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
#st.plotly_chart(fig)


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
fig.add_trace(go.Scatter(
    x=df_3pm['datetime'],
    y=df_3pm['high'],
    mode='markers+text',
    name='3PM High',
    marker=dict(color='orange', size=8, symbol='triangle-up'),
    text=["High"] * len(df_3pm),
    textposition="top center"
))

fig.add_trace(go.Scatter(
    x=df_3pm['datetime'],
    y=df_3pm['low'],
    mode='markers+text',
    name='3PM Low',
    marker=dict(color='cyan', size=8, symbol='triangle-down'),
    text=["Low"] * len(df_3pm),
    textposition="bottom center"
))

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
