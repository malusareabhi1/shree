import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from math import floor

# Title
st.title("📈 Swing Trade Strategy")

# Sidebar options
capital = st.sidebar.number_input("Total Capital (₹)", value=100000)
risk_percent = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Detect and set datetime index
    datetime_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()), None)
    if not datetime_col:
        st.error("❌ No datetime column found.")
        st.stop()
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df.set_index(datetime_col, inplace=True)
    st.success(f"✅ Using '{datetime_col}' as index.")

    # Ensure OHLC columns
    for col in ['Open','High','Low','Close']:
        if col not in df.columns:
            st.error(f"❌ '{col}' column missing.")
            st.stop()

    # Calculate indicators
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['Signal'] = None
    df.loc[df['SMA_20'] > df['SMA_50'], 'Signal'] = 'BUY'
    df.loc[df['SMA_20'] < df['SMA_50'], 'Signal'] = 'SELL'

    # Build complete trade log with stoploss, target, quantity
    trades = []
    in_trade = False
    entry_time = entry_price = stop_loss = target1 = target2 = qty = None
    risk_per_trade = capital * (risk_percent / 100)

    for time, row in df.iterrows():
        sig = row['Signal']
        price = row['Close']
        low = row['Low']

        if sig == 'BUY' and not in_trade:
            entry_time = time
            entry_price = price
            stop_loss = low
            risk = entry_price - stop_loss
            if risk <= 0:
                continue
            qty = floor(risk_per_trade / risk)
            target1 = entry_price + 1.5 * risk
            target2 = entry_price + 2.5 * risk
            in_trade = True

        elif in_trade:
            if price <= stop_loss:
                # Stop loss hit
                exit_time = time
                exit_price = price
                pnl = (exit_price - entry_price) * qty
                trades.append({
                    'Entry Time': entry_time, 'Entry Price': entry_price,
                    'Exit Time': exit_time, 'Exit Price': exit_price,
                    'Qty': qty, 'Exit Type': 'Stop Loss', 'PnL': round(pnl, 2)
                })
                in_trade = False

            elif price >= target2:
                # Target 2 hit
                exit_time = time
                exit_price = target2
                pnl = (exit_price - entry_price) * qty
                trades.append({
                    'Entry Time': entry_time, 'Entry Price': entry_price,
                    'Exit Time': exit_time, 'Exit Price': exit_price,
                    'Qty': qty, 'Exit Type': 'Target 2', 'PnL': round(pnl, 2)
                })
                in_trade = False

            elif sig == 'SELL':
                # Manual exit
                exit_time = time
                exit_price = price
                pnl = (exit_price - entry_price) * qty
                trades.append({
                    'Entry Time': entry_time, 'Entry Price': entry_price,
                    'Exit Time': exit_time, 'Exit Price': exit_price,
                    'Qty': qty, 'Exit Type': 'SELL Signal', 'PnL': round(pnl, 2)
                })
                in_trade = False

    trade_log = pd.DataFrame(trades)

    # Summary metrics
    if not trade_log.empty:
        trade_log['Cumulative PnL'] = trade_log['PnL'].cumsum()
        total_pnl = trade_log['PnL'].sum()
        win_rate = (trade_log['PnL'] > 0).sum() / len(trade_log) * 100
        avg_pnl = trade_log['PnL'].mean()

        st.metric("Total PnL", f"₹{total_pnl:.2f}")
        st.metric("Win Rate", f"{win_rate:.2f}%")
        st.metric("Avg PnL per Trade", f"₹{avg_pnl:.2f}")

        st.dataframe(trade_log)
        st.line_chart(trade_log.set_index('Exit Time')['Cumulative PnL'])

        csv = trade_log.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Trade Log", data=csv, file_name="swing_trade_log.csv", mime="text/csv")

    # Candlestick chart + signals
    fig = go.Figure([go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
    )])
    buys = df[df['Signal'] == 'BUY']
    sells = df[df['Signal'] == 'SELL']
    fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', marker=dict(symbol='triangle-up', color='green', size=12), name='BUY'))
    fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=12), name='SELL'))
    fig.update_layout(title="Swing Trade Chart", xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)
