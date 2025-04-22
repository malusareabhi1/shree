import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, time as dt_time
import pytz
import time
from kiteconnect import KiteTicker

# ===== Telegram Setup =====
bot_token = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
chat_id = "1320205499"

def send_telegram(msg):
    try:
        res = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
        )
        if res.status_code != 200:
            st.warning("⚠️ Telegram message failed to send.")
    except Exception as e:
        st.warning(f"⚠️ Telegram error: {e}")

# ===== Market Open Check (India NSE) =====
def is_market_open():
    now = datetime.now(pytz.timezone("Asia/Kolkata")).time()
    return dt_time(9, 15) <= now <= dt_time(15, 30)

# ===== Streamlit App =====
st.set_page_config("📉 Strategy Tester", layout="centered")
st.title("📊 Doctor Strategy (Test + Live NSEI Mode)")

if is_market_open():
    st.success("📈 Market is Open — Running Live Strategy on ^NSEI")

    from kiteconnect import KiteConnect
    kite = st.session_state.get("kite")

    if kite is None:
        st.error("🔌 Kite session not found. Please login through 'KITE API' tab first.")
        st.stop()

    live_placeholder = st.empty()
    symbol = "NSE:NIFTY 50"
    capital = 50000
    qty = 10

    entry_price = None
    trailing_sl = None

    while is_market_open():
        try:
            ltp = kite.ltp([symbol])[symbol]['last_price']

            if entry_price is None:
                entry_price = ltp
                trailing_sl = entry_price - 5
                send_telegram(f"📥 <b>LIVE BUY SIGNAL</b>\n<b>Symbol:</b> ^NSEI\n<b>Price:</b> ₹{entry_price}\n<b>Qty:</b> {qty}")
            elif ltp >= entry_price + 5:
                trailing_sl = ltp - 5
                send_telegram(f"🔁 <b>LIVE Trailing SL Moved</b>\n<b>New SL:</b> ₹{trailing_sl}")
            elif ltp <= trailing_sl:
                send_telegram(f"📤 <b>LIVE SELL SIGNAL</b>\n<b>Symbol:</b> ^NSEI\n<b>Exit:</b> ₹{ltp}\n<b>Reason:</b> SL Hit")
                break

            with live_placeholder.container():
                st.metric("Live Price (^NSEI)", f"₹{ltp}")
                st.metric("Entry Price", f"₹{entry_price}")
                st.metric("Trailing SL", f"₹{trailing_sl}")
                st.metric("Qty", qty)

            time.sleep(10)

        except Exception as e:
            st.error(f"❌ Live Error: {e}")
            break

else:
    st.warning("📴 Market is closed — testing strategy on uploaded CSV data.")

    uploaded_file = st.file_uploader("📂 Upload CSV file", type="csv")
    capital = st.number_input("💰 Capital", value=50000)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully")

        if "Close" not in df.columns:
            st.error("CSV must contain a 'Close' column")
        else:
            df['Signal'] = df['Close'].diff().apply(lambda x: 'BUY' if x > 5 else 'SELL' if x < -5 else None)
            df.dropna(subset=['Signal'], inplace=True)

            trade_log = pd.DataFrame({
                "Date": df['Date'],
                "Stock": "TEST-STOCK",
                "Action": df['Signal'],
                "Price": df['Close'],
                "Qty": 10,
                "PnL": df['Close'].diff().fillna(0) * 10
            })

            for _, row in trade_log.iterrows():
                send_telegram(
                    f"<b>{row['Action']} SIGNAL</b>\n"
                    f"<b>Stock:</b> {row['Stock']}\n"
                    f"<b>Price:</b> ₹{row['Price']}\n"
                    f"<b>Qty:</b> {row['Qty']}\n"
                    f"<b>Date:</b> {row['Date']}"
                )

            net_pnl = trade_log["PnL"].sum()
            win_trades = trade_log[trade_log["PnL"] > 0].shape[0]
            lose_trades = trade_log[trade_log["PnL"] < 0].shape[0]
            last_order = f"{trade_log.iloc[-1]['Action']} - TEST-STOCK - 10 shares @ {trade_log.iloc[-1]['Price']}"

            st.session_state['net_pnl'] = float(net_pnl)
            st.session_state['used_capital'] = capital
            st.session_state['open_positions'] = {"TEST-STOCK": {"Qty": 10, "Avg Price": round(df['Close'].iloc[-1], 2)}}
            st.session_state['last_order'] = last_order

            st.metric("Net PnL", f"₹{net_pnl:.2f}")
            st.metric("Winning Trades", win_trades)
            st.metric("Losing Trades", lose_trades)
            st.dataframe(trade_log)

            csv = trade_log.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Trade Log", data=csv, file_name="trade_log.csv", mime="text/csv")
            st.session_state['trade_log_df'] = trade_log

            fig = go.Figure(data=[go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
            )])

            buy_signals = df[df['Signal'] == 'BUY']
            sell_signals = df[df['Signal'] == 'SELL']

            fig.add_trace(go.Scatter(
                x=buy_signals['Date'],
                y=buy_signals['Close'],
                mode='markers',
                name='Buy Signal',
                marker=dict(symbol='triangle-up', color='green', size=12)
            ))

            fig.add_trace(go.Scatter(
                x=sell_signals['Date'],
                y=sell_signals['Close'],
                mode='markers',
                name='Sell Signal',
                marker=dict(symbol='triangle-down', color='red', size=12)
            ))

            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Price (₹)',
                xaxis_rangeslider_visible=False,
                template='plotly_dark',
                hovermode='x unified',
            )

            st.plotly_chart(fig)

            df['Signal_Code'] = df['Signal'].map({'BUY': 1, 'SELL': -1})
            csv_with_signal = df[["Date", "Open", "High", "Low", "Close", "Signal_Code"]]
            csv_data = csv_with_signal.rename(columns={"Signal_Code": "Signal"}).to_csv(index=False).encode("utf-8")

            st.download_button(
                label="📥 Download CSV with Signals",
                data=csv_data,
                file_name="signal_output.csv",
                mime="text/csv"
            )
