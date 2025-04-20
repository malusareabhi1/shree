import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Doctor2.0 Strategy", layout="wide")

# Sidebar menu
menu = ["Home", "Doctor2.0 Strategy"]
selected = st.sidebar.selectbox("Select Page", menu)

if selected == "Doctor2.0 Strategy":
    st.title("⚙️ Test Doctor2.0 Strategy")

    uploaded_file = st.file_uploader("Upload 5-minute Nifty/Bank Nifty CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        # Check required columns
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            st.error("CSV missing required columns.")
            st.stop()

        # Convert and prepare datetime
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df.set_index('Date', inplace=True)

        # Calculate Bollinger Bands (20 SMA)
        df['20sma'] = df['Close'].rolling(window=20).mean()
        df['stddev'] = df['Close'].rolling(window=20).std()
        df['upper_band'] = df['20sma'] + 2 * df['stddev']
        df['lower_band'] = df['20sma'] - 2 * df['stddev']

        # Track trades
        trades = []
        cooldown = 5  # to avoid frequent trades
        last_trade_index = -cooldown

        for i in range(21, len(df)-2):
            if i - last_trade_index < cooldown:
                continue

            candle = df.iloc[i]
            prev_candle = df.iloc[i-1]

            # Step 2-4: 20 SMA Cross & confirmation
            crossed_up = prev_candle['Close'] < prev_candle['20sma'] and candle['Close'] > candle['20sma']
            closed_above = candle['Close'] > candle['20sma'] and candle['Low'] > candle['20sma']

            if crossed_up and closed_above:
                reference_candle = candle
                prev2_candle = df.iloc[i-2]

                ref_level = max(prev2_candle['High'], prev2_candle['Close'])
                next_candle = df.iloc[i+1]

                is_bullish = next_candle['Close'] > next_candle['Open']

                if next_candle['High'] > ref_level and is_bullish:
                    entry_price = ref_level
                    sl_price = entry_price * 0.90
                    target1 = entry_price * 1.05
                    target2 = entry_price * 1.10
                    target3 = entry_price * 1.15
                    final_target = entry_price * 1.20

                    # Simulate outcome
                    result = "Open"
                    for j in range(i+2, min(i+20, len(df))):
                        high = df.iloc[j]['High']
                        low = df.iloc[j]['Low']
                        if low < sl_price:
                            result = "SL"
                            break
                        elif high >= final_target:
                            result = "T4"
                            break
                        elif high >= target3:
                            result = "T3"
                        elif high >= target2:
                            result = "T2"
                        elif high >= target1:
                            result = "T1"

                    trades.append({
                        'Entry Time': next_candle.name,
                        'Entry Price': round(entry_price, 2),
                        'SL': round(sl_price, 2),
                        'T1': round(target1, 2),
                        'T2': round(target2, 2),
                        'T3': round(target3, 2),
                        'T4': round(final_target, 2),
                        'Reference High': round(ref_level, 2),
                        'Outcome': result
                    })
                    last_trade_index = i

        # Display trades
        st.subheader("📈 Doctor2.0 Strategy Trades")
        if trades:
            trades_df = pd.DataFrame(trades)
            st.dataframe(trades_df)

            # Downloadable CSV
            csv = trades_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Trade Log", csv, "doctor2_trades.csv", "text/csv")
        else:
            st.warning("No valid trades found based on strategy rules.")

        # Plot chart
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'], high=df['High'],
            low=df['Low'], close=df['Close'], name="Candles"
        ))
        fig.add_trace(go.Scatter(x=df.index, y=df['20sma'], line=dict(color='blue'), name="20 SMA"))

        st.plotly_chart(fig, use_container_width=True)
