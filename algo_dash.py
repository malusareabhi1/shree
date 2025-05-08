import streamlit as st
import pandas as pd
import numpy as np
import time
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Algo Trading Dashboard", layout="wide")

# Sidebar
st.sidebar.title("📈 Algo Dashboard")
section = st.sidebar.radio("Navigate", ["Live Trading", "Backtest", "Trade Log", "Settings"])

# Dummy trade log for display
trade_log_df = pd.DataFrame(columns=["Time", "Symbol", "Side", "Qty", "Price", "Status"])

# Header
st.title("💹 Algo Trading Dashboard")

# Live Trading Section
if section == "Live Trading":
    st.subheader("🚀 Live Trading Control")

    strategy = st.selectbox("Select Strategy", ["Doctor Strategy", "ORB", "Momentum", "Mean Reversion"])
    is_live = st.toggle("Activate Live Trading")

    col1, col2, col3 = st.columns(3)
    col1.metric("🔢 Trades Today", "14", "+3")
    col2.metric("💰 Total PnL", "₹12,350", "+₹1,200")
    col3.metric("📊 Win Rate", "68%", "↑")

    # Placeholder for live chart
    st.subheader("📉 Live Price Chart")

    # Simulated data (replace with real-time feed)
    df = pd.DataFrame({
        "time": pd.date_range(end=pd.Timestamp.now(), periods=100, freq="T"),
        "price": np.cumsum(np.random.randn(100)) + 15000
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["time"], y=df["price"], mode="lines", name="Price"))
    st.plotly_chart(fig, use_container_width=True)

    # Session state for persistent logging
    if "trade_log" not in st.session_state:
        st.session_state.trade_log = []
    
    if is_live:
        st.success("Live trading is active")
    
        status_placeholder = st.empty()
        log_placeholder = st.empty()
    
        for i in range(10):  # Simulate 10 live updates
            # Simulated live price
            live_price = round(df['price'].iloc[-1] + np.random.randn(), 2)
            current_time = pd.Timestamp.now().strftime("%H:%M:%S")
    
            # ==== Basic Doctor Strategy Simulation ====
            signal = "Hold"
            if live_price > df['price'].iloc[-1] + 2:
                signal = "Buy"
            elif live_price < df['price'].iloc[-1] - 2:
                signal = "Sell"
    
            # Show live signal
            status_placeholder.markdown(f"### 📢 Signal: **{signal}** at ₹{live_price} ({current_time})")
    
            # Log the trade if actionable
            if signal in ["Buy", "Sell"]:
                st.session_state.trade_log.append({
                    "Time": current_time,
                    "Symbol": "NIFTY",
                    "Side": signal,
                    "Qty": 50,
                    "Price": live_price,
                    "Status": "Executed"
                })
    
            # Refresh trade log table
            log_df = pd.DataFrame(st.session_state.trade_log)
            log_placeholder.dataframe(log_df, use_container_width=True)
    
            time.sleep(2)


    # Trade Log
    st.subheader("📘 Trade Log")
    st.dataframe(trade_log_df, use_container_width=True)

    st.download_button("Download Log", trade_log_df.to_csv(index=False).encode(), "trade_log.csv")

    if st.button("🛑 Stop Trading"):
        st.warning("Trading stopped manually.")
        # Add logic to stop background process

# Backtest Section
elif section == "Backtest":
    st.subheader("🧪 Backtest Strategy")
    st.info("Upload your historical data and test your strategy here.")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Data preview:")
        st.dataframe(df.head())

# Trade Log Section
elif section == "Trade Log":
    st.subheader("📋 All Trades History")
    # Load from file or DB
    st.dataframe(trade_log_df)

# Settings Section
elif section == "Settings":
    st.subheader("⚙️ API & Config Settings")
    api_key = st.text_input("Enter Broker API Key", type="password")
    secret_key = st.text_input("Enter API Secret", type="password")
    telegram_token = st.text_input("Telegram Bot Token", type="password")
    if st.button("Save Settings"):
        st.success("Settings saved securely.")

