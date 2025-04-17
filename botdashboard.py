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

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    capital = st.number_input("Capital Allocation (₹)", value=50000)

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
                "PnL": df['Close'].diff().fillna(0) * 10  # Example
            })

            net_pnl = trade_log["PnL"].sum()
            win_trades = trade_log[trade_log["PnL"] > 0].shape[0]
            lose_trades = trade_log[trade_log["PnL"] < 0].shape[0]
            last_order = f"{trade_log.iloc[-1]['Action']} - TEST-STOCK - 10 shares @ {trade_log.iloc[-1]['Price']}"

            # ✅ Store to session state for Account Info
            st.session_state['net_pnl'] = float(net_pnl)
            st.session_state['used_capital'] = capital
            st.session_state['open_positions'] = {"TEST-STOCK": {"Qty": 10, "Avg Price": round(df['Close'].iloc[-1], 2)}}
            st.session_state['last_order'] = last_order

            # Results
            st.metric("Net PnL", f"₹{net_pnl:.2f}")
            st.metric("Winning Trades", win_trades)
            st.metric("Losing Trades", lose_trades)
            st.dataframe(trade_log)

            csv = trade_log.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Trade Log", data=csv, file_name="trade_log.csv", mime="text/csv")


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

    starting_capital = 100000
    net_pnl = st.session_state.get('net_pnl', 0)
    used_capital = st.session_state.get('used_capital', 0)
    available_capital = starting_capital + net_pnl

    open_positions = st.session_state.get('open_positions', {})
    last_order = st.session_state.get('last_order', "No order placed yet")

    # Display
    st.subheader("Funds Summary")
    st.json({
        "Available Capital": round(available_capital, 2),
        "Used Capital": round(used_capital, 2),
        "Net PnL": round(net_pnl, 2)
    })

    st.subheader("Open Positions")
    st.json(open_positions)

    st.subheader("Last Order")
    st.write(last_order)

