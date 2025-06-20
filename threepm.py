import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

st.title("📈 NIFTY 3PM Breakout with 10-Point Move")

symbol = "^NSEI"  # Nifty 50 Index
interval = "15m"
points_required = 10

st.write("Fetching last 30 days of 15-minute NIFTY data...")
data = yf.download(symbol, period="30d", interval=interval)
data.dropna(inplace=True)

# Prepare data
data['Date'] = data.index.date
data['Time'] = data.index.time

# Find 3:00 PM candles
three_pm_time = datetime.strptime("15:00:00", "%H:%M:%S").time()
three_pm_close = data[data['Time'] == three_pm_time][['Close']]
three_pm_close = three_pm_close.rename(columns={'Close': '3PM_Close'})
three_pm_close['Date'] = three_pm_close.index.date
three_pm_close['NextDate'] = three_pm_close['Date'].shift(-1)


# Extract full 3:00 PM candle data
three_pm_candles = data[data['Time'] == three_pm_time].copy()
three_pm_candles_display = three_pm_candles[['Open', 'High', 'Low', 'Close']]
three_pm_candles_display['Date'] = three_pm_candles.index.date
three_pm_candles_display.reset_index(drop=True, inplace=True)

st.subheader("📋 3:00 PM Candle Data (Past Days)")
st.dataframe(three_pm_candles_display)


# Reset index to remove datetime index
three_pm_candles.reset_index(inplace=True)

# Extract date only (optional: keep datetime for precision)
three_pm_candles['Date'] = three_pm_candles['Datetime'].dt.date

# Select desired columns
three_pm_display = three_pm_candles[['Date', 'Open', 'High', 'Low', 'Close']]

# Show in Streamlit
st.subheader("📋 3:00 PM Candle Data (Past Days)")
st.dataframe(three_pm_display)


# Result list
results = []

# Loop through each next trading day
for i in range(len(three_pm_close) - 1):
    prev_close = three_pm_close.iloc[i]['3PM_Close']
    next_date = three_pm_close.iloc[i]['NextDate']
    next_day_data = data[data['Date'] == next_date]

    crossed = False
    breakout_index = None
    high_after = None

    for j in range(1, len(next_day_data)):
        prev_c = next_day_data.iloc[j - 1]
        curr_c = next_day_data.iloc[j]

        if prev_c['Close'] < prev_close and curr_c['Close'] > prev_close:
            crossed = True
            breakout_index = curr_c.name
            high_after = next_day_data.iloc[j:]['High'].max()
            break

    if crossed and high_after >= (prev_close + points_required):
        results.append({
            'Date': next_date,
            'Prev_3PM_Close': prev_close,
            'Breakout_Time': breakout_index,
            'High_After': high_after
        })

# Show results
st.subheader(f"✅ Found {len(results)} Breakout Days")
if results:
    df_result = pd.DataFrame(results)
    st.dataframe(df_result)

    # Select a breakout date to visualize
    selected_date = st.selectbox("📅 Select a breakout date to view chart:", df_result['Date'])

    # Extract that day's data
    chart_data = data[data['Date'] == selected_date]
    prev_close_level = df_result[df_result['Date'] == selected_date]['Prev_3PM_Close'].values[0]
    breakout_time = df_result[df_result['Date'] == selected_date]['Breakout_Time'].values[0]

    # Plot
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=chart_data.index,
        open=chart_data['Open'],
        high=chart_data['High'],
        low=chart_data['Low'],
        close=chart_data['Close'],
        name="Candles"
    ))

    # 3PM Close Line
    fig.add_hline(y=prev_close_level, line=dict(color="blue", dash="dash"), 
                  annotation_text="Previous 3PM Close", annotation_position="top left")

    # Breakout Marker
    fig.add_trace(go.Scatter(
        x=[breakout_time],
        y=[prev_close_level],
        mode='markers+text',
        marker=dict(color='red', size=12, symbol='triangle-up'),
        name="Breakout",
        text=["Breakout"],
        textposition="top center"
    ))

    fig.update_layout(
        title=f"NIFTY Breakout on {selected_date}",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No matching breakouts found in recent data.")
