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
             # Create download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{stock.upper()}_{interval}_data.csv",
            mime="text/csv"
        )

elif selected == "Test Strategy":
    st.title("⚙️ Test Doctor Trade Strategy")
    uploaded_file = st.file_uploader("Upload Stock Data (CSV)", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully!")
        st.write("📋 Data Preview", df.head())

        # Make sure 'Date' is in datetime format
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        capital = st.number_input("Capital Allocation (₹)", value=50000)

        if st.button("Run Backtest"):
            st.info("Running Doctor Strategy...")

            # Placeholder Doctor Strategy Logic — Replace with your actual logic
            df['Signal'] = df['Close'].diff().apply(lambda x: 'BUY' if x > 5 else 'SELL' if x < -5 else None)
            df['PnL'] = df['Close'].diff().fillna(0)
            df['PnL'] = df.apply(lambda row: row['PnL'] if row['Signal'] in ['BUY', 'SELL'] else 0, axis=1)

            # Filter out only trades
            trade_log = df[df['Signal'].notnull()].copy()
            trade_log = trade_log[['Date', 'Signal', 'Close', 'PnL']]
            trade_log.rename(columns={"Signal": "Action", "Close": "Price"}, inplace=True)
            trade_log['Qty'] = 1  # Placeholder qty

            # Metrics
            total_pnl = trade_log['PnL'].sum()
            win_trades = len(trade_log[trade_log['PnL'] > 0])
            lose_trades = len(trade_log[trade_log['PnL'] < 0])
            hit_ratio = round((win_trades / (win_trades + lose_trades)) * 100, 2) if (win_trades + lose_trades) > 0 else 0

            st.metric("Net PnL", f"₹{total_pnl:,.2f}")
            st.metric("Winning Trades", win_trades)
            st.metric("Losing Trades", lose_trades)
            st.metric("Hit Ratio", f"{hit_ratio}%")

            # Equity curve
            df['Equity Curve'] = capital + df['PnL'].cumsum()
            st.subheader("📈 Equity Curve")
            st.line_chart(df.set_index("Date")["Equity Curve"])

            # Show trade log table
            st.subheader("📝 Trade Log")
            st.dataframe(trade_log)

elif selected == "Trade Log":
    st.title("📝 Trade Log")
    trade_data = pd.DataFrame({
        "Date": ["2024-04-15", "2024-04-16"],
        "Stock": ["INFY", "TCS"],
        "Action": ["BUY", "SELL"],
        "Price": [1450.5, 3125.0],
        "Qty": [50, 30],
        "PnL": [2500, -750]
    })
    st.dataframe(trade_data)

elif selected == "Account Info":
    st.title("💼 Account Information")
    st.subheader("Funds")
    st.json({"Available": 120000, "Used": 50000})
    st.subheader("Open Positions")
    st.json({"TCS": {"Qty": 30, "Avg Price": 3125.0}, "INFY": {"Qty": 50, "Avg Price": 1450.5}})
    st.subheader("Orders")
    st.json({"Last Order": "SELL - TCS - 30 Shares @ 3150"})
