import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from io import BytesIO

# Optional: For email alerts (setup needed)
# import smtplib
# from email.mime.text import MIMEText

# --- Doctor Trade Strategy with PnL, Capital, Risk ---
def doctor_trade_strategy(df, capital=100000, risk_per_trade=0.02):
    df['Signal'] = 0
    df['MA'] = df['Close'].rolling(window=5).mean()
    df.loc[df['Close'] > df['MA'], 'Signal'] = 1
    df.loc[df['Close'] < df['MA'], 'Signal'] = -1
    df['Position'] = df['Signal'].shift(1)
    df['Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Returns'] * df['Position']
    df['Cumulative Strategy Returns'] = (1 + df['Strategy_Returns'].fillna(0)).cumprod()
    df['Cumulative Market Returns'] = (1 + df['Returns'].fillna(0)).cumprod()

    trades = []
    in_trade = False
    entry_price = 0
    for i in range(1, len(df)):
        if df['Signal'].iloc[i] == 1 and not in_trade:
            in_trade = True
            entry_price = df['Close'].iloc[i]
            entry_time = df.index[i]
        elif df['Signal'].iloc[i] == -1 and in_trade:
            exit_price = df['Close'].iloc[i]
            exit_time = df.index[i]
            qty = int((capital * risk_per_trade) / abs(exit_price - entry_price)) if exit_price != entry_price else 0
            pnl = (exit_price - entry_price) * qty
            trades.append({
                'Entry Time': entry_time,
                'Entry Price': entry_price,
                'Exit Time': exit_time,
                'Exit Price': exit_price,
                'Quantity': qty,
                'PnL': round(pnl, 2)
            })
            in_trade = False

    trade_log = pd.DataFrame(trades)
    return df, trade_log

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("📈 Doctor Trade Strategy Dashboard")

uploaded_file = st.file_uploader("📁 Upload your stock CSV file", type=["csv"])
capital = st.number_input("💰 Capital (₹)", min_value=1000, value=100000)
risk = st.slider("⚖️ Risk per Trade (%)", 1, 10, 2)

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Parse date
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

        # Check required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            st.error("CSV must contain: Open, High, Low, Close, Volume")
        else:
            df, trade_log = doctor_trade_strategy(df.copy(), capital=capital, risk_per_trade=risk/100)

            # Plotting Price with Buy/Sell markers
            st.subheader("📊 Price Chart with Buy/Sell Signals")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Close", line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=df[df['Signal'] == 1].index, y=df[df['Signal'] == 1]['Close'],
                                     mode='markers', marker_symbol='triangle-up', marker_color='green',
                                     marker_size=10, name='Buy'))
            fig.add_trace(go.Scatter(x=df[df['Signal'] == -1].index, y=df[df['Signal'] == -1]['Close'],
                                     mode='markers', marker_symbol='triangle-down', marker_color='red',
                                     marker_size=10, name='Sell'))
            st.plotly_chart(fig, use_container_width=True)

            # Trade Log
            st.subheader("🧠 Trade Log with PnL")
            st.dataframe(trade_log)

            # Profit Summary
            if not trade_log.empty:
                total_pnl = trade_log['PnL'].sum()
                total_trades = len(trade_log)
                win_trades = trade_log[trade_log['PnL'] > 0].shape[0]
                loss_trades = total_trades - win_trades

                st.markdown(f"""
                **Total Trades:** {total_trades}  
                ✅ **Winning Trades:** {win_trades}  
                ❌ **Losing Trades:** {loss_trades}  
                💹 **Net PnL:** ₹ {round(total_pnl, 2)}
                """)

            # Performance Chart
            st.subheader("📈 Strategy vs Market Returns")
            st.line_chart(df[['Cumulative Market Returns', 'Cumulative Strategy Returns']])

            # Export Trade Log
            st.download_button(
                label="📥 Download Trade Log",
                data=trade_log.to_csv(index=False).encode(),
                file_name="trade_log.csv",
                mime="text/csv"
            )

            # Optional: Send Email (Set up credentials)
            # if st.button("📧 Send Trade Log via Email"):
            #     msg = MIMEText(trade_log.to_csv(index=False))
            #     msg['Subject'] = "Doctor Strategy Trade Log"
            #     msg['From'] = "you@example.com"
            #     msg['To'] = "recipient@example.com"
            #     with smtplib.SMTP("smtp.gmail.com", 587) as server:
            #         server.starttls()
            #         server.login("you@example.com", "yourpassword")
            #         server.send_message(msg)
            #     st.success("📨 Email sent successfully!")

            st.success("✅ Strategy executed with capital and risk logic.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
