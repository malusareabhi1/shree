import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
# Page configuration
st.set_page_config(layout="wide", page_title="Doctor Trade Dashboard")

# Sidebar navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Doctor Trade",
        options=["Dashboard", "Get Stock Data", "Test Strategy", "Trade Log", "Account Info"],
        icons=["bar-chart", "search", "cpu", "clipboard-data", "wallet2"],
        menu_icon="cast",
        default_index=0,
    )

# Main area rendering
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .card {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            padding: 20px;
            margin: 10px 0;
        }
        .card-title {
            font-size: 18px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

if selected == "Dashboard":
    st.title("📊 Welcome to Doctor Trade Dashboard")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Capital Overview</div>", unsafe_allow_html=True)
        st.metric(label="Available Capital", value="₹1,20,000")
        st.metric(label="Used Capital", value="₹50,000")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<div class='card-title'>Strategy Overview</div>", unsafe_allow_html=True)
        st.metric(label="Hit Ratio", value="61.76%")
        st.metric(label="Risk per Trade", value="1.5%")
        st.markdown('</div>', unsafe_allow_html=True)

elif selected == "Get Stock Data":
    st.title("📈 Get Stock Data from NSE")

    nifty_50_stocks = [
        "^NSEI", "ADANIENT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
        "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
        "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFC.NS",
        "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
        "INDUSINDBK.NS", "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS",
        "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS",
        "SBIN.NS", "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS",
        "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
    ]

    stock = st.selectbox("Select NIFTY 50 stock or Index (^NSEI)", options=nifty_50_stocks, index=nifty_50_stocks.index("TCS.NS"))
    from_date = st.date_input("From Date", datetime(2025, 1, 1))
    to_date = st.date_input("To Date", datetime.today())
    interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], index=5)

    if st.button("Fetch Data"):
        st.info(f"Fetching data for {stock.upper()} from {from_date} to {to_date} at interval {interval}")
        try:
            df = yf.download(stock, start=from_date, end=to_date, interval=interval)
            if df.empty:
                st.warning("No data returned. Check symbol or market hours for intraday intervals.")
            else:
                df.reset_index(inplace=True)
                st.dataframe(df)

                # CSV download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{stock.upper()}_{interval}_data.csv",
                    mime="text/csv"
                )

                # Show Close price chart
                if "Date" in df.columns and "Close" in df.columns:
                    fig = px.line(df, x="Date", y="Close", title=f"{stock} Close Price")
                    st.plotly_chart(fig)
                else:
                    st.warning("Could not find 'Date' and 'Close' columns to generate chart.")
        except Exception as e:
            st.error(f"Error fetching data: {e}")


          
elif selected == "Test Strategy":
    st.title("⚙️ Test Doctor Trade Strategy (Advanced)")

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    capital = st.number_input("Capital Allocation (₹)", value=50000)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        if "Close" not in df.columns or "Date" not in df.columns:
            st.error("CSV must contain 'Date' and 'Close' columns")
        else:
            st.success("File uploaded successfully")

            df['Date'] = pd.to_datetime(df['Date'])
            df.sort_values('Date', inplace=True)
            df.reset_index(drop=True, inplace=True)

            # 🎯 Strategy: Bollinger Band Breakout + ATR Filter
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['STD20'] = df['Close'].rolling(window=20).std()
            df['Upper'] = df['MA20'] + 2 * df['STD20']
            df['Lower'] = df['MA20'] - 2 * df['STD20']
            df['ATR'] = (df['High'] - df['Low']).rolling(window=14).mean()  # add High/Low in your CSV

            df['Signal'] = None
            position = False
            entry_price = 0
            stop_loss = 0

            for i in range(1, len(df)):
                if not position and df['Close'].iloc[i] > df['Upper'].iloc[i - 1]:
                    df.at[i, 'Signal'] = 'BUY'
                    entry_price = df['Close'].iloc[i]
                    stop_loss = entry_price - df['ATR'].iloc[i] * 1.5
                    position = True
                elif position and (df['Close'].iloc[i] < df['MA20'].iloc[i - 1] or df['Close'].iloc[i] < stop_loss):
                    df.at[i, 'Signal'] = 'SELL'
                    position = False

            df.dropna(subset=['Signal'], inplace=True)

            # 💼 Trade Simulation
            trade_log = []
            qty = 0
            last_price = 0
            equity_curve = []
            balance = capital

            for idx, row in df.iterrows():
                if row['Signal'] == 'BUY':
                    last_price = row['Close']
                    qty = int(capital // last_price)
                    trade_log.append({
                        "Date": row['Date'],
                        "Stock": "TEST-STOCK",
                        "Action": "BUY",
                        "Price": last_price,
                        "Qty": qty,
                        "PnL": 0
                    })
                elif row['Signal'] == 'SELL' and qty > 0:
                    sell_price = row['Close']
                    pnl = (sell_price - last_price) * qty
                    balance += pnl
                    trade_log.append({
                        "Date": row['Date'],
                        "Stock": "TEST-STOCK",
                        "Action": "SELL",
                        "Price": sell_price,
                        "Qty": qty,
                        "PnL": pnl
                    })
                    equity_curve.append({"Date": row['Date'], "Equity": balance})
                    qty = 0

            trade_log_df = pd.DataFrame(trade_log)
            equity_df = pd.DataFrame(equity_curve)

            net_pnl = trade_log_df["PnL"].sum()
            total_trades = trade_log_df.shape[0] // 2
            win_trades = trade_log_df[trade_log_df["PnL"] > 0].shape[0]
            lose_trades = trade_log_df[trade_log_df["PnL"] < 0].shape[0]
            avg_profit = trade_log_df["PnL"].mean()
            win_rate = (win_trades / (win_trades + lose_trades) * 100) if (win_trades + lose_trades) > 0 else 0

            last_order = (
                f"{trade_log_df.iloc[-1]['Action']} - TEST-STOCK - {trade_log_df.iloc[-1]['Qty']} shares @ ₹{trade_log_df.iloc[-1]['Price']:.2f}"
                if not trade_log_df.empty else "No trades"
            )

            # ✅ Store session state
            st.session_state['net_pnl'] = float(net_pnl)
            st.session_state['used_capital'] = capital
            st.session_state['open_positions'] = {"TEST-STOCK": {"Qty": qty, "Avg Price": round(last_price, 2)}}
            st.session_state['last_order'] = last_order
            st.session_state['trade_log_df'] = trade_log_df

            # 📊 Metrics
            st.metric("Net PnL", f"₹{net_pnl:.2f}")
            st.metric("Win Rate", f"{win_rate:.2f}%")
            st.metric("Avg Profit per Trade", f"₹{avg_profit:.2f}")
            st.metric("Winning Trades", win_trades)
            st.metric("Losing Trades", lose_trades)

            # 📈 Equity Curve
            if not equity_df.empty:
                fig = px.line(equity_df, x="Date", y="Equity", title="📈 Equity Curve Over Time")
                st.plotly_chart(fig, use_container_width=True)

            # 📋 Trade Log
            st.subheader("📝 Trade Log")
            st.dataframe(trade_log_df)

            # ⬇️ Download
            csv = trade_log_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Trade Log", data=csv, file_name="trade_log.csv", mime="text/csv")

            # 💬 Telegram alert simulation
            with st.expander("📢 Telegram Alert Simulation"):
                for idx, row in trade_log_df.iterrows():
                    msg = f"🟢 {row['Action']} {row['Stock']} @ ₹{row['Price']} | Qty: {row['Qty']} | PnL: ₹{row['PnL']:.2f}"
                    st.write(msg)

elif selected == "Trade Log":
    st.title("📘 Trade Log")

    # Check if trade_log_df exists
    if 'trade_log_df' in st.session_state and not st.session_state['trade_log_df'].empty:
        trade_log = st.session_state['trade_log_df']
        
        st.subheader("Trade Log Table")
        st.dataframe(trade_log)

        # 📉 PnL Over Time Chart
        st.subheader("PnL Over Time")
        pnl_chart = px.line(trade_log, x="Timestamp", y="PnL", title="PnL Over Time")
       # st.plotly_chart(pnl_chart, use_container_width=True)

        # 🥧 Win/Loss Pie Chart
        st.subheader("Win/Loss Ratio")
        win_count = (trade_log['PnL'] > 0).sum()
        loss_count = (trade_log['PnL'] <= 0).sum()
        win_loss_df = pd.DataFrame({
            "Result": ["Win", "Loss"],
            "Count": [win_count, loss_count]
        })
        fig = px.pie(win_loss_df, names='Result', values='Count', title='Win vs Loss')
        #st.plotly_chart(fig, use_container_width=True)

        # 📁 Download option
        csv = trade_log.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Trade Log as CSV",
            data=csv,
            file_name='trade_log.csv',
            mime='text/csv'
        )
    else:
        st.info("No trade log found. Run 'Test Strategy' first.")


elif selected == "Account Info":
    st.title("💼 Account Information")

    # Get session values
    starting_capital = 100000
    net_pnl = st.session_state.get('net_pnl', 0)
    used_capital = st.session_state.get('used_capital', 0)
    available_capital = starting_capital + net_pnl

    open_positions = st.session_state.get('open_positions', {})
    last_order = st.session_state.get('last_order', "No order placed yet")

    # 📊 Display Funds Summary
    st.subheader("Funds Summary")
    funds_df = pd.DataFrame({
        "Metric": ["Available Capital", "Used Capital", "Net PnL"],
        "Value (₹)": [round(available_capital, 2), round(used_capital, 2), round(net_pnl, 2)]
    })
    st.table(funds_df)

    # 📊 Display Open Positions
    st.subheader("Open Positions")
    if open_positions:
        positions_df = pd.DataFrame([
            {"Stock": stock, "Qty": data["Qty"], "Avg Price": data["Avg Price"]}
            for stock, data in open_positions.items()
        ])
        st.table(positions_df)
    else:
        st.write("No open positions.")

    # 🧾 Last Order
    st.subheader("Last Order")
    st.write(last_order) 
