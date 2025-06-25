import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="NIFTY 15-Min Chart", layout="wide")
st.title("📈 NIFTY 15-Min Chart – Last 60 Days")

# Mode selection: online fetch or CSV upload
mode = st.sidebar.radio("Select data source:", ["Fetch Online", "Upload CSV"])

if mode == "Fetch Online":
    with st.spinner("Fetching NIFTY 15-min data..."):
        ticker = "^NSEI"
        df = yf.download(ticker, interval="15m", period="60d", progress=False)
        df.columns = df.columns.get_level_values(-0)
        df.reset_index(inplace=True)
        datetime_col = df.columns[0]
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        df[datetime_col] = df[datetime_col].dt.tz_convert('Asia/Kolkata')
        df = df.rename(columns={datetime_col: 'datetime'})

elif mode == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        # Find datetime-like column
        datetime_col_candidates = [col for col in df.columns if "date" in col.lower() or "time" in col.lower()]
        if not datetime_col_candidates:
            st.error("No datetime column found in uploaded CSV!")
            st.stop()
        datetime_col = datetime_col_candidates[0]
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        # Localize timezone if naive
        if df[datetime_col].dt.tz is None:
            df[datetime_col] = df[datetime_col].dt.tz_localize('Asia/Kolkata')
        df = df.rename(columns={datetime_col: 'datetime'})
    else:
        st.info("Please upload a CSV file to proceed.")
        st.stop()

# Lowercase columns for consistency
df.columns = df.columns.str.lower()

# Remove off-market hours (before 9:15 AM or after 3:30 PM IST)
df = df[(df['datetime'].dt.time >= pd.to_datetime("09:15").time()) &
        (df['datetime'].dt.time <= pd.to_datetime("15:30").time())]

# Filter to last 20 trading days
df['date'] = df['datetime'].dt.date
last_20_trading_days = sorted(df['date'].unique())[-20:]
df = df[df['date'].isin(last_20_trading_days)]
df = df.drop(columns='date')

# Filter 3PM candles (hour == 15 and minute == 0)
df_3pm = df[(df['datetime'].dt.hour == 15) & (df['datetime'].dt.minute == 0)]

# === Trade log: Next day breaks 3PM high + 100 points ===
trade_log = []

for i in range(len(df_3pm) - 1):  # avoid last day, no next day after it
    current_row = df_3pm.iloc[i]
    next_row = df_3pm.iloc[i + 1]

    threepm_date = current_row['datetime'].date()
    next_day_date = next_row['datetime'].date()

    threepm_high = current_row['high']
    target = threepm_high + 100

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
        'Target (High + 100)': round(target, 2),
        'Hit?': '✅ Yes' if hit else '❌ No',
        'Hit Time': hit_time.time() if hit else '-'
    })

trade_log_df = pd.DataFrame(trade_log)

# === Additional trade log: Cross below 3PM close and drop 100 points ===
close_breakdown_log = []

for i in range(len(df_3pm) - 1):
    current_row = df_3pm.iloc[i]
    next_day_date = df_3pm.iloc[i + 1]['datetime'].date()

    threepm_close = current_row['close']
    target_down = threepm_close - 100

    next_day_data = df[df['datetime'].dt.date == next_day_date].copy()
    if next_day_data.empty:
        continue

    next_day_data.sort_values(by='datetime', inplace=True)

    crossed_down = False
    target_hit = False
    hit_time = None

    for j in range(1, len(next_day_data)):
        prev_candle = next_day_data.iloc[j - 1]
        this_candle = next_day_data.iloc[j]

        # Check crossing close from above to below
        if not crossed_down and prev_candle['high'] > threepm_close and this_candle['low'] < threepm_close:
            crossed_down = True
            cross_time = this_candle['datetime']

        # After crossing, check drop 100 points
        if crossed_down and this_candle['low'] <= target_down:
            target_hit = True
            hit_time = this_candle['datetime']
            break

    close_breakdown_log.append({
        '3PM Date': current_row['datetime'].date(),
        'Next Day': next_day_date,
        '3PM Close': round(threepm_close, 2),
        'Target (Close - 100)': round(target_down, 2),
        'Crossed & Dropped 100?': '✅ Yes' if target_hit else '❌ No',
        'Drop Hit Time': hit_time.time() if hit_time else '-'
    })

breakdown_df = pd.DataFrame(close_breakdown_log)

# Check required columns exist
required_cols = ['datetime', 'open', 'high', 'low', 'close']
if not all(col in df.columns for col in required_cols):
    missing = [col for col in required_cols if col not in df.columns]
    st.error(f"Missing columns: {missing}")
    st.stop()

# Show dataframe sample
st.dataframe(df.head())

# Plot candlestick chart
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
    title="NIFTY 15-Min Chart (Last 20 Trading Days)",
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

# Show trade log 1
st.subheader("📘 Trade Log – Did Next Day Break 3PM High + 100 Points?")
st.dataframe(trade_log_df)

success_count = trade_log_df[trade_log_df['Hit?'] == '✅ Yes'].shape[0]
total_checked = trade_log_df.shape[0]

st.markdown(f"### 📊 Summary: 3PM High + 100 Point Breakout")
st.success(f"✅ This scenario happened **{success_count} times** out of **{total_checked}** trading days.")

st.download_button(
    label="📥 Download Trade Log as CSV",
    data=trade_log_df.to_csv(index=False),
    file_name="nifty_3pm_breakout_tradelog.csv",
    mime="text/csv"
)

# Show trade log 2
st.subheader("📉 Breakdown Log – Did Price Cross Below 3PM Close and Drop 100 Points?")
st.dataframe(breakdown_df)

count = breakdown_df[breakdown_df['Crossed & Dropped 100?'] == '✅ Yes'].shape[0]
st.success(f"✅ This scenario happened **{count} times** in the last {len(df_3pm)-1} trading days.")

st.download_button(
    label="📥 Download Breakdown Log as CSV",
    data=breakdown_df.to_csv(index=False),
    file_name="nifty_3pm_breakdown_tradelog.csv",
    mime="text/csv"
)
