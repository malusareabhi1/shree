import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# Helper function to align timezone
def align_timezone(dt):
    dt = pd.to_datetime(dt)  # Make sure it's a datetime object
    if dt.tzinfo is None:
        return dt.tz_localize("UTC").tz_convert("Asia/Kolkata")
    return dt.tz_convert("Asia/Kolkata")

# Streamlit UI
st.title("⚙️ Test Doctor Trade Strategy")

uploaded_file = st.file_uploader("Upload CSV file", type="csv")
capital = st.number_input("Capital Allocation (₹)", value=50000)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded successfully")

    # Convert 'Date' to datetime if it's not already
    df['Date'] = pd.to_datetime(df['Date'])

    # Check if the 'Date' column is timezone-aware
    if df['Date'].dt.tz is None:
        df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    else:
        df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')

    # Filter times for 9:30 AM to 1:30 PM market hours
    df = df[df['Date'].dt.time.between(pd.to_datetime('09:30:00').time(), pd.to_datetime('13:30:00').time())]

    # Display the final DataFrame
    st.write(df.head())

    if "Close" not in df.columns:
        st.error("CSV must contain a 'Close' column")
    else:
        # Step 1: Time Frame (5-minute chart)
        if df['Date'].diff().dt.total_seconds().median() < 300:
            df = df.resample('5T', on='Date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
        df.dropna(inplace=True)

        # Step 2: Center Line (20 SMA) and Bollinger Bands
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
        df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()

        # Step 3: Cross and Confirm Closing Above SMA
        df['Crossed_SMA_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) < df['SMA_20'].shift(1))

        # Step 4: Reference Candle - Next Candle Close Above 20 SMA
        df['Ref_Candle_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) > df['SMA_20'].shift(1))

        # Step 5: IV Condition (Placeholder IV value)
        iv_data = 9.18  # Placeholder value, replace with actual API fetch for IV

        # Step 6: Signal Logic
        df['Signal'] = None
        df['Signal_Reason'] = None  # Add this new column
        for idx in range(1, len(df)):
            if df['Ref_Candle_Up'].iloc[idx] and iv_data >= 16:
                if df['Close'].iloc[idx] > df['Close'].iloc[idx - 1]:  # Confirm Next Candle Cross
                    df.at[idx, 'Signal'] = 'BUY'
                    df.at[idx, 'Signal_Reason'] = "Ref Candle Up & IV >= 16 & Confirmed Next Candle"

        # Step 7: Stop Loss Logic (10% below entry price)
        df['Stop_Loss'] = df['Close'] * 0.90

        # Step 8: Profit Booking and Trailing Stop Loss
        df['Initial_Stop_Loss'] = df['Close'] * 0.90
        df['Profit_Target'] = df['Close'] * 1.05

        trades = []
        for idx in range(1, len(df)):
            if df['Signal'].iloc[idx] == 'BUY':
                entry_price = df['Close'].iloc[idx]
                stop_loss = entry_price * 0.90
                profit_target = entry_price * 1.05
                trade = {
                    'Entry_Time': df['Date'].iloc[idx],
                    'Entry_Price': entry_price,
                    'Stop_Loss': stop_loss,
                    'Profit_Target': profit_target,
                    'Exit_Time': None,
                    'Exit_Price': None,
                    'Brokerage': 20,  # ₹20 per trade
                    'PnL': None,
                    'Turnover': None,
                    'Exit_Reason': None,
                    'PnL_After_Brokerage': None,
                    'Signal_Reason': '20 SMA Cross + IV >= 16'
                }
                trades.append(trade)

        # Display the chart with trade signals
        fig = go.Figure(data=[go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            increasing_line_color='green',
            decreasing_line_color='red',
        )])

        # Add buy signals to the chart
        buy_signals = df[df['Signal'] == 'BUY']
        fig.add_trace(go.Scatter(
            x=buy_signals['Date'],
            y=buy_signals['Close'],
            mode='markers',
            name='Buy Signal',
            marker=dict(symbol='triangle-up', color='green', size=12)
        ))

        # Add 20-period SMA to the chart
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['SMA_20'],
            mode='lines',
            name='20 SMA',
            line=dict(color='blue', width=2)
        ))

        # Display the chart
        st.subheader("Daily Chart")
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Price (₹)',
            xaxis_rangeslider_visible=False,
            template='plotly_dark',
            hovermode='x unified',
        )
        st.plotly_chart(fig)

        # Create trade log DataFrame
        trade_log_df = pd.DataFrame(trades)

        # Display trade log
        st.subheader("Trade Log")
        st.dataframe(trade_log_df)

        # Ensure proper columns for performance summary
        if 'Turnover' not in trade_log_df.columns:
            trade_log_df['Turnover'] = trade_log_df['Entry_Price'] + trade_log_df['Exit_Price']
        if 'PnL_After_Brokerage' not in trade_log_df.columns:
            trade_log_df['PnL_After_Brokerage'] = trade_log_df['PnL'] - trade_log_df['Brokerage']

        # Compute summary stats
        total_trades = len(trade_log_df)
        wins = trade_log_df[trade_log_df['PnL_After_Brokerage'] > 0]
        losses = trade_log_df[trade_log_df['PnL_After_Brokerage'] < 0]
        num_wins = len(wins)
        num_losses = len(losses)
        win_rate = (num_wins / total_trades * 100) if total_trades else 0

        gross_profit = wins['PnL_After_Brokerage'].sum()
        gross_loss = losses['PnL_After_Brokerage'].sum()  # negative number
        profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else float("inf")

        avg_win = wins['PnL_After_Brokerage'].mean() if num_wins else 0
        avg_loss = losses['PnL_After_Brokerage'].mean() if num_losses else 0

        # Total Turnover & Brokerage
        total_turnover = trade_log_df['Turnover'].sum()
        total_brokerage = trade_log_df['Brokerage'].sum()

        # Expectancy per trade
        expectancy = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss

        # Display performance summary
        st.markdown("## 📊 Performance Summary")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Trades", total_trades)
        c2.metric("Winning Trades", num_wins, f"{win_rate:.1f}%")
        c3.metric("Losing Trades", num_losses)

        c4, c5, c6 = st.columns(3)
        c4.metric("Gross Profit", f"₹{gross_profit:.2f}")
        c5.metric("Gross Loss", f"₹{gross_loss:.2f}")
        c6.metric("Profit Factor", f"{profit_factor:.2f}")

        c7, c8, c9 = st.columns(3)
        c7.metric("Avg. Win", f"₹{avg_win:.2f}")
        c8.metric("Avg. Loss", f"₹{avg_loss:.2f}")
        c9.metric("Expectancy", f"₹{expectancy:.2f}")

        c10, c11, c12 = st.columns(3)
        c10.metric("Total Turnover", f"₹{total_turnover:.2f}")
        c11.metric("Total Brokerage", f"₹{total_brokerage:.2f}")
        c12.metric("Expectancy", f"₹{expectancy:.2f}")

        # Display equity curve
        st.markdown("### 📈 Equity Curve")
        st.line_chart(trade_log_df['PnL_After_Brokerage'].cumsum())

        # Download full log
        csv = trade_log_df.to_csv(index=False)
        st.download_button(
            "📥 Download Trade Log",
            data=csv,
            file_name="trade_log_with_summary.csv",
            mime="text/csv",
            key="download_with_summary"
        )
