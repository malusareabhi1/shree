import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Doctor2.0 Strategy", layout="wide")

# Sidebar menu
menu = ["Home", "Doctor2.0 Strategy"]
selected = st.sidebar.selectbox("Select Page", menu)

if selected == "Doctor2.0 Strategy":
    st.title("⚙️ Test Doctor2.0 Strategy")

    uploaded_file = st.file_uploader("Upload 5-minute Nifty/Bank Nifty CSV file", type=["csv"])
    capital = st.number_input("Enter Total Capital (₹)", min_value=1000, value=100000)
    risk_per_trade_pct = st.slider("Risk per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            st.error("CSV missing required columns.")
            st.stop()

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df.set_index('Date', inplace=True)

        df['20sma'] = df['Close'].rolling(window=20).mean()
        df['stddev'] = df['Close'].rolling(window=20).std()
        df['upper_band'] = df['20sma'] + 2 * df['stddev']
        df['lower_band'] = df['20sma'] - 2 * df['stddev']

        # Drop rows with NaN from indicator columns
        df.dropna(subset=['20sma', 'stddev'], inplace=True)

        trades = []
        cooldown = 5
        last_trade_index = -cooldown

        for i in range(2, len(df)-2):
            if i - last_trade_index < cooldown:
                continue

            candle = df.iloc[i]
            prev_candle = df.iloc[i-1]

            crossed_up = prev_candle['Close'] < prev_candle['20sma'] and candle['Close'] > candle['20sma']
            closed_above = candle['Close'] > candle['20sma']

            if crossed_up and closed_above:
                reference_candle = candle
                prev2_candle = df.iloc[i-2]

                ref_level = max(prev2_candle['High'], prev2_candle['Close'])
                next_candle = df.iloc[i+1]

                if next_candle['High'] > ref_level:
                    entry_price = ref_level
                    sl_price = entry_price * 0.90
                    target1 = entry_price * 1.05
                    target2 = entry_price * 1.10
                    target3 = entry_price * 1.15
                    final_target = entry_price * 1.20

                    quantity = int((capital * (risk_per_trade_pct / 100)) / (entry_price - sl_price))
                    result = "Open"
                    outcome_index = None

                    for j in range(i+2, min(i+20, len(df))):
                        high = df.iloc[j]['High']
                        low = df.iloc[j]['Low']
                        if low < sl_price:
                            result = "SL"
                            outcome_index = j
                            break
                        elif high >= final_target:
                            result = "T4"
                            outcome_index = j
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
                        'Outcome': result,
                        'Quantity': quantity,
                        'Exit Time': df.index[outcome_index] if outcome_index else None
                    })
                    last_trade_index = i

        st.subheader("📈 Doctor2.0 Strategy Trades")
        if trades:
            trades_df = pd.DataFrame(trades)
            st.dataframe(trades_df)

            csv = trades_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Trade Log", csv, "doctor2_trades.csv", "text/csv")

            # Backtest Performance Summary
            outcomes = trades_df['Outcome'].value_counts().to_dict()
            total_trades = len(trades_df)
            win_trades = sum([outcomes.get(k, 0) for k in ['T1', 'T2', 'T3', 'T4']])
            win_rate = round((win_trades / total_trades) * 100, 2)
            st.markdown(f"**Total Trades:** {total_trades} | **Win Rate:** {win_rate}%")

            # Equity Curve
            pnl = []
            for _, row in trades_df.iterrows():
                if row['Outcome'] == 'SL':
                    profit = (row['SL'] - row['Entry Price']) * row['Quantity']
                else:
                    tgt_map = {'T1': row['T1'], 'T2': row['T2'], 'T3': row['T3'], 'T4': row['T4']}
                    profit = (tgt_map.get(row['Outcome'], row['Entry Price']) - row['Entry Price']) * row['Quantity']
                pnl.append(profit)

            equity_curve = pd.Series(pnl).cumsum()
            st.line_chart(equity_curve)

            # Plot chart
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'], name="Candles"
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['20sma'], line=dict(color='blue'), name="20 SMA"))

            for trade in trades:
                fig.add_trace(go.Scatter(
                    x=[trade['Entry Time']], y=[trade['Entry Price']],
                    mode='markers', marker=dict(color='blue', size=10), name='Entry 🔵'
                ))
                fig.add_trace(go.Scatter(
                    x=[trade['Exit Time']], y=[trade['SL'] if trade['Outcome'] == 'SL' else trade[trade['Outcome']]],
                    mode='markers', marker=dict(color='red' if trade['Outcome']=='SL' else 'green', size=10),
                    name='SL 🔻' if trade['Outcome']=='SL' else 'TP 🟢'
                ))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid trades found based on strategy rules.")
