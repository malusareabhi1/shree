import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd
import yfinance as yf
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
    st.title("📈 Get Stock Data")
    stock = st.text_input("Enter NSE stock symbol (e.g., TCS.NS, INFY.NS)", value="TCS.NS")
    from_date = st.date_input("From Date", datetime(2023, 1, 1))
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
                st.line_chart(df.set_index("Date")["Close"])
        except Exception as e:
            st.error(f"Error fetching data: {e}")
               

elif selected == "Test Strategy":
    st.title("⚙️ Test Doctor Trade Strategy")
    stock = st.selectbox("Select Stock", ["RELIANCE", "TCS", "INFY", "HDFCBANK"])
    capital = st.number_input("Capital Allocation (₹)", value=50000)
    uploaded_file = st.file_uploader("📁 Upload CSV File (OHLCV Data)", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        if st.button("Run Backtest"):
            try:
                # Check if 'Close' and 'Date' columns are present
                if 'Close' not in df.columns or 'Date' not in df.columns:
                    st.error("CSV must contain 'Date' and 'Close' columns.")
                else:
                    df['Signal'] = df['Close'].diff().apply(lambda x: 'BUY' if x > 5 else 'SELL' if x < -5 else None)
                    df.dropna(subset=['Signal'], inplace=True)

                    pnl = df['Signal'].apply(lambda x: 500 if x == 'BUY' else -250).sum()
                    winning_trades = (df['Signal'] == 'BUY').sum()
                    losing_trades = (df['Signal'] == 'SELL').sum()

                    st.success(f"Strategy tested on {stock} with capital ₹{capital}")
                    st.metric("Net PnL", f"₹{pnl}")
                    st.metric("Winning Trades", winning_trades)
                    st.metric("Losing Trades", losing_trades)

                    st.subheader("📋 Trade Log")
                    trade_log = df[['Date', 'Signal', 'Close']].rename(columns={
                        'Signal': 'Action',
                        'Close': 'Price'
                    })
                    trade_log['Stock'] = stock
                    trade_log['Qty'] = 10  # Example quantity
                    trade_log['PnL'] = trade_log['Action'].apply(lambda x: 500 if x == 'BUY' else -250)
                    trade_log = trade_log[['Date', 'Stock', 'Action', 'Price', 'Qty', 'PnL']]
                    st.dataframe(trade_log)

                    # Download button
                    csv = trade_log.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Trade Log CSV",
                        data=csv,
                        file_name="doctor_strategy_trade_log.csv",
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Error during strategy test: {e}")


elif selected == "Trade Log":
    st.title("📝 Trade Log")

    uploaded_log = st.file_uploader("📁 Upload Trade Log CSV", type=["csv"])

    if uploaded_log is not None:
        try:
            trade_data = pd.read_csv(uploaded_log)

            if all(col in trade_data.columns for col in ["PnL", "Action", "Stock", "Date"]):
                # Ensure Date is in datetime format
                trade_data["Date"] = pd.to_datetime(trade_data["Date"])

                # Metrics
                total_pnl = trade_data["PnL"].sum()
                win_trades = (trade_data["PnL"] > 0).sum()
                loss_trades = (trade_data["PnL"] < 0).sum()
                unique_stocks = trade_data["Stock"].nunique()

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📈 Net PnL", f"₹{total_pnl}")
                col2.metric("✅ Winning Trades", win_trades)
                col3.metric("❌ Losing Trades", loss_trades)
                col4.metric("📊 Stocks Traded", unique_stocks)

                # Line chart: PnL over time
                st.subheader("📅 PnL Over Time")
                pnl_over_time = trade_data.groupby("Date")["PnL"].sum().reset_index()
                st.line_chart(pnl_over_time.set_index("Date"))

                # Pie chart: Win vs Loss
                st.subheader("🥧 Win/Loss Ratio")
                pie_data = pd.Series([win_trades, loss_trades], index=["Wins", "Losses"])
                st.pyplot(pie_data.plot.pie(autopct="%1.1f%%", figsize=(5, 5), title="Win/Loss Ratio").figure)

                # Trade Log Table
                st.subheader("📋 Trade Log Table")
                st.dataframe(trade_data)

            else:
                st.warning("CSV must include columns: Date, Stock, Action, Price, Qty, PnL")

        except Exception as e:
            st.error(f"Failed to read uploaded file: {e}")
    else:
        # Example data when no file is uploaded
        trade_data = pd.DataFrame({
            "Date": ["2024-04-15", "2024-04-16"],
            "Stock": ["INFY", "TCS"],
            "Action": ["BUY", "SELL"],
            "Price": [1450.5, 3125.0],
            "Qty": [50, 30],
            "PnL": [2500, -750]
        })

        st.info("No file uploaded. Showing example trade log.")
        st.dataframe(trade_data)


elif selected == "Account Info":
    st.title("💼 Account Information")

    uploaded_log = st.file_uploader("📁 Upload Trade Log CSV", type=["csv"], key="account_info_log")

    if uploaded_log is not None:
        try:
            trade_data = pd.read_csv(uploaded_log)

            # Ensure required columns
            required_cols = {"Date", "Stock", "Action", "Price", "Qty", "PnL"}
            if required_cols.issubset(trade_data.columns):
                # Convert Date
                trade_data["Date"] = pd.to_datetime(trade_data["Date"])
                
                # Calculate Net PnL
                net_pnl = trade_data["PnL"].sum()
                starting_capital = 100000
                available_capital = starting_capital + net_pnl

                # Open Positions
                positions = {}

                for _, row in trade_data.iterrows():
                    stock = row["Stock"]
                    qty = row["Qty"]
                    price = row["Price"]
                    action = row["Action"]

                    if stock not in positions:
                        positions[stock] = {"Qty": 0, "Cost": 0}

                    if action == "BUY":
                        prev_qty = positions[stock]["Qty"]
                        prev_cost = positions[stock]["Cost"]
                        new_qty = prev_qty + qty
                        new_cost = prev_cost + qty * price
                        positions[stock]["Qty"] = new_qty
                        positions[stock]["Cost"] = new_cost
                    elif action == "SELL":
                        positions[stock]["Qty"] -= qty
                        positions[stock]["Cost"] -= qty * price

                # Remove closed positions
                open_positions = {k: v for k, v in positions.items() if v["Qty"] > 0}

                # Format open positions
                formatted_positions = {}
                for stock, pos in open_positions.items():
                    avg_price = round(pos["Cost"] / pos["Qty"], 2) if pos["Qty"] > 0 else 0
                    formatted_positions[stock] = {
                        "Qty": pos["Qty"],
                        "Avg Price": avg_price
                    }

                used_capital = sum(v["Qty"] * v["Avg Price"] for v in formatted_positions.values())

                # Last Order Summary
                last_trade = trade_data.sort_values("Date").iloc[-1]
                last_order = f"{last_trade['Action']} - {last_trade['Stock']} - {last_trade['Qty']} Shares @ {last_trade['Price']}"

                # Display
                st.subheader("Funds Summary")
                st.json({
                    "Available": round(available_capital, 2),
                    "Used": round(used_capital, 2),
                    "Net PnL": round(net_pnl, 2)
                })

                st.subheader("Open Positions")
                st.json(formatted_positions)

                st.subheader("Last Order")
                st.write(last_order)
            else:
                st.warning("CSV must include columns: Date, Stock, Action, Price, Qty, PnL")
        except Exception as e:
            st.error(f"Error processing file: {e}")

    else:
        # Fallback when no file uploaded
        st.subheader("Funds Summary")
        st.json({"Available": 120000, "Used": 50000})
        st.subheader("Open Positions")
        st.json({
            "TCS": {"Qty": 30, "Avg Price": 3125.0},
            "INFY": {"Qty": 50, "Avg Price": 1450.5}
        })
        st.subheader("Last Order")
        st.write("SELL - TCS - 30 Shares @ 3150")

