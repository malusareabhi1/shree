import streamlit as st
import pandas as pd
import numpy as np
import datetime

def detect_doctor2_strategy(df, iv):
    results = []
    
    if iv < 16:
        return results

    df['20_SMA'] = df['close'].rolling(window=20).mean()
    df['above_20_sma'] = df['close'] > df['20_SMA']
    
    for i in range(21, len(df)-2):
        time_check = df.iloc[i].name.time() > datetime.time(9, 30)
        cross_up = df['close'].iloc[i] > df['20_SMA'].iloc[i] and df['close'].iloc[i-1] < df['20_SMA'].iloc[i-1]
        ref_cond = df['close'].iloc[i+1] > df['20_SMA'].iloc[i+1] and df['low'].iloc[i+1] > df['20_SMA'].iloc[i+1]

        if time_check and cross_up and ref_cond:
            pre_ref_high = df['high'].iloc[i-1]
            ref_close = df['close'].iloc[i+1]
            breakout_level = max(pre_ref_high, ref_close)
            breakout_candle = df.iloc[i+2]

            if breakout_candle['low'] < breakout_level < breakout_candle['close']:
                entry_price = breakout_level
                sl = entry_price * 0.90
                t1 = entry_price * 1.05
                t2 = entry_price * 1.10
                t3 = entry_price * 1.15
                t4 = entry_price * 1.20
                results.append({
                    'entry_time': breakout_candle.name,
                    'entry_price': round(entry_price, 2),
                    'stop_loss': round(sl, 2),
                    'targets': [round(t1, 2), round(t2, 2), round(t3, 2), round(t4, 2)]
                })

    return results

# Streamlit App
st.set_page_config(layout="wide")
st.title("Doctor2.0 Strategy Scanner")

with st.sidebar:
    st.header("Strategy Settings")
    uploaded_file = st.file_uploader("Upload 5-min OHLC CSV")
    iv_value = st.number_input("NIFTY/BankNIFTY IV", min_value=0.0, value=18.0, step=0.1)

    st.markdown("""
    **Strategy Logic:**

    1. Bollinger Band 20 SMA cross from below.
    2. Close above SMA and next candle also closes above without touching it.
    3. Check reference candle rules.
    4. Confirm breakout and trade initiation.
    5. Entry/SL/Target logic.
    6. IV must be 16 or more.
    """)

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=['datetime'], index_col='datetime')
    st.dataframe(df.tail())

    signals = detect_doctor2_strategy(df, iv_value)

    if signals:
        st.success(f"{len(signals)} signal(s) found")
        st.dataframe(pd.DataFrame(signals))
    else:
        st.warning("No signals found. Check IV or conditions.")
else:
    st.info("Upload a 5-minute OHLC file to begin.")
