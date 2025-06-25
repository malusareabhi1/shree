import streamlit as st
import pandas as pd
import pytz
import plotly.graph_objects as go

# --- Breakout Logic ---
def mark_3pm_breakouts(df):
    df = df.copy()
    df['date'] = df['datetime'].dt.date
    df['time'] = df['datetime'].dt.time

    # Identify 3:00 PM candle per day
    mask_3pm = df['datetime'].dt.hour == 15
    mask_3pm &= df['datetime'].dt.minute == 0
    df_3pm = df.loc[mask_3pm, ['date', 'high', 'low']].copy()
    df_3pm = df_3pm.rename(columns={'high': '3pm_high', 'low': '3pm_low'})
    df_3pm['next_date'] = pd.to_datetime(df_3pm['date']) + pd.Timedelta(days=1)
    df_3pm = df_3pm.set_index('next_date')[['3pm_high', '3pm_low']]

    # Join 3PM high/low with main DataFrame
    df['date'] = pd.to_datetime(df['date'])
    df = df.join(df_3pm, on='date')

    # Breakout flags
    df['break_above'] = (df['high'] > df['3pm_high']) & df['3pm_high'].notna()
    df['break_below'] = (df['low'] < df['3pm_low']) & df['3pm_low'].notna()

    return df

# --- Streamlit UI ---
st.set_page_config(page_title="3PM Candle Breakout Detector", layout="wide")
st.title("📈 3PM Candle Breakout Detector")

uploaded_file = st.file_uploader("Upload 15-min OHLC CSV (with datetime column)", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Select datetime column
    datetime_col = st.selectbox("Select datetime column", options=df.columns)
    
    # Parse datetime and convert to IST
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df['datetime'] = df[datetime_col].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    
    # Standard column names (handle case-insensitivity)
    df.columns = [col.lower() for col in df.columns]
    df = df.rename(columns={
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close'
    })

    # Drop missing values
    df = df[['datetime', 'open', 'high', 'low', 'close']].dropna()

    # Run breakout logic
    df = mark_3pm_breakouts(df)

    # --- Display Table ---
    st.subheader("📋 Breakout Table (Last 50 Rows)")
    st.dataframe(df[['datetime', 'open', 'high', 'low', 'close', '3pm_high', '3pm_low', 'break_above', 'break_below']].tail(50))

    # --- Candlestick Chart ---
    st.subheader("📊 Breakout Visualization")

    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='NIFTY Price'
    )])

    # Plot previous 3PM high/low
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['3pm_high'],
        mode='lines', line=dict(color='green', width=1),
        name='Prev 3PM High'
    ))

    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['3pm_low'],
        mode='lines', line=dict(color='red', width=1),
        name='Prev 3PM Low'
    ))

    # Breakout markers
    breakout_up = df[df['break_above']]
    breakout_down = df[df['break_below']]

    fig.add_trace(go.Scatter(
        x=breakout_up['datetime'], y=breakout_up['high'] + 10,
        mode='markers', marker=dict(color='lime', size=10, symbol='triangle-up'),
        name='Break Above'
    ))

    fig.add_trace(go.Scatter(
        x=breakout_down['datetime'], y=breakout_down['low'] - 10,
        mode='markers', marker=dict(color='red', size=10, symbol='triangle-down'),
        name='Break Below'
    ))

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=10, r=10, t=30, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Please upload a 15-min candle CSV file to get started.")
