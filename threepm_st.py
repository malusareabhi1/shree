import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def mark_3pm_breakouts(df):
    df = df.copy()
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['date'] = df['datetime'].dt.date
    df['time'] = df['datetime'].dt.time

    mask_3pm = df['time'] == pd.to_datetime("15:00:00").time()
    df_3pm = df.loc[mask_3pm, ['date', 'high', 'low']].copy()
    df_3pm = df_3pm.rename(columns={'high':'3pm_high', 'low':'3pm_low'})

    df_3pm['date'] = pd.to_datetime(df_3pm['date'])
    df_3pm['next_date'] = df_3pm['date'] + pd.Timedelta(days=1)
    df_3pm = df_3pm.set_index('next_date')[['3pm_high','3pm_low']]

    df['date'] = pd.to_datetime(df['date'])
    df = df.join(df_3pm, on='date')

    df['break_above'] = (df['high'] > df['3pm_high']) & (~df['3pm_high'].isna())
    df['break_below'] = (df['low'] < df['3pm_low']) & (~df['3pm_low'].isna())

    return df

st.title("3PM Candle Breakout Detector")

uploaded_file = st.file_uploader("Upload CSV with columns: datetime, open, high, low, close", type=['csv'])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df['datetime'] = pd.to_datetime(df['datetime'])
    # Convert and localize to IST
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['datetime'] = df['datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')

    df = mark_3pm_breakouts(df)

    st.subheader("Data with Breakout Flags")
    st.dataframe(df[['datetime', 'open', 'high', 'low', 'close', '3pm_high', '3pm_low', 'break_above', 'break_below']].tail(50))

    st.subheader("Candlestick Chart with Breakouts")

    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='Price'
    )])

    # Plot 3PM high and low levels (line only where defined)
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['3pm_high'],
        mode='lines', line=dict(color='green', width=1),
        name='Prev Day 3PM High'
    ))
    fig.add_trace(go.Scatter(
        x=df['datetime'], y=df['3pm_low'],
        mode='lines', line=dict(color='red', width=1),
        name='Prev Day 3PM Low'
    ))

    # Highlight breakout candles
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

    fig.update_layout(xaxis_rangeslider_visible=False, height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Upload a CSV file to get started")
