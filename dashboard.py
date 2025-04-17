import streamlit as st
import pandas as pd
import datetime
import random
import plotly.graph_objects as go
from nsepython import nse_eq
import requests
import smtplib
from email.mime.text import MIMEText

# --- App Configuration ---
st.set_page_config(page_title="Algo Trading Dashboard", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
        .main { background-color: #f0f2f6; }
        h1, h2, h3 { color: #003366; }
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.image("https://via.placeholder.com/150x80?text=Algo+Trade", use_column_width=True)
st.sidebar.title("📊 Trading Console")
selected_tab = st.sidebar.radio("Navigate", ["Live Market", "Trade Book", "Capital Overview", "Analytics"])

# --- Dummy Data Functions ---
def get_dummy_trade_data():
    return pd.DataFrame([
        {"Stock": "RELIANCE", "Qty": 50, "Buy_Price": 2450, "Sell_Price": 2480, "Used_Capital": 122500, "PnL": 1500, "Time": "10:30 AM"},
        {"Stock": "TCS", "Qty": 30, "Buy_Price": 3150, "Sell_Price": 3190, "Used_Capital": 94500, "PnL": 1200, "Time": "11:00 AM"},
    ])

def get_dummy_funds():
    return pd.DataFrame({"Available Funds": [1500000], "Used Capital": [217000], "Net PnL": [2700]})

# --- Telegram Alerts ---
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# --- Email Alerts ---
EMAIL_SENDER = "sender@example.com"
EMAIL_PASSWORD = "yourpassword"
EMAIL_RECEIVER = "receiver@example.com"
SMTP_SERVER = "smtp.gmail.com"


def send_email_alert(subject, message):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# --- Live Data from NSE ---
@st.cache_data(ttl=300)
def fetch_live_stock_data(symbol):
    try:
        data = nse_eq(symbol)
        price_info = data.get("priceInfo", {})
        return {
            "last_price": price_info.get("lastPrice", "NA"),
            "day_high": price_info.get("intraDayHighLow", {}).get("max", "NA"),
            "day_low": price_info.get("intraDayHighLow", {}).get("min", "NA"),
        }
    except Exception as e:
        return {"error": str(e)}

# --- Data Load ---
trade_log = get_dummy_trade_data()
funds_df = get_dummy_funds()

# --- Live Market Tab ---
if selected_tab == "Live Market":
    st.title("📈 Market Monitor")

    col1, col2, col3 = st.columns(3)
    col1.metric("Used Capital", f"₹{funds_df['Used Capital'].iloc[0]:,.2f}")
    col2.metric("Net PnL", f"₹{funds_df['Net PnL'].iloc[0]:,.2f}", delta=f"{round((funds_df['Net PnL'].iloc[0] / funds_df['Used Capital'].iloc[0])*100, 2)}%")
    col3.metric("Total Trades", len(trade_log))

    st.markdown("---")

    st.subheader("📡 Live Stock Price")
    stock = st.selectbox("Select a stock", ["RELIANCE", "TCS", "INFY", "HDFCBANK"])
    live_data = fetch_live_stock_data(stock)

    if "error" not in live_data:
        st.success(f"**{stock}** 📍 ₹{live_data['last_price']} (High: ₹{live_data['day_high']} / Low: ₹{live_data['day_low']})")
        if st.button("🔔 Send Alert"):
            alert_msg = f"Live Update - {stock}: ₹{live_data['last_price']} (High: ₹{live_data['day_high']} / Low: ₹{live_data['day_low']})"
            send_telegram_alert(alert_msg)
            send_email_alert(f"Live Alert - {stock}", alert_msg)
            st.info("Alert sent via Telegram & Email!")
    else:
        st.error(f"Failed to fetch data: {live_data['error']}")

    st.subheader("📊 Stock Price Chart")
    dummy_prices = pd.DataFrame({
        "Time": pd.date_range(start=datetime.datetime.now(), periods=50, freq='5min'),
        "Open": [random.randint(1000, 1100) for _ in range(50)],
        "High": [random.randint(1100, 1150) for _ in range(50)],
        "Low": [random.randint(980, 1050) for _ in range(50)],
        "Close": [random.randint(1020, 1120) for _ in range(50)]
    })

    fig = go.Figure(data=[go.Candlestick(
        x=dummy_prices['Time'],
        open=dummy_prices['Open'],
        high=dummy_prices['High'],
        low=dummy_prices['Low'],
        close=dummy_prices['Close']
    )])
    fig.update_layout(height=400, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# --- Trade Book Tab ---
elif selected_tab == "Trade Book":
    st.title("📒 Trade Log")
    st.dataframe(trade_log, use_container_width=True)

# --- Capital Overview Tab ---
elif selected_tab == "Capital Overview":
    st.title("💰 Capital & Performance")
    st.table(funds_df)

    st.subheader("📌 Capital Usage")
    used = funds_df['Used Capital'].iloc[0]
    available = funds_df['Available Funds'].iloc[0]
    total = used + available
    st.progress(used / total)
    st.markdown(f"**{round((used/total)*100, 2)}% capital used**")

# --- Analytics Tab ---
elif selected_tab == "Analytics":
    st.title("📈 Analytics & Insights")

    st.subheader("Profit & Loss by Stock")
    grouped = trade_log.groupby("Stock")["PnL"].sum().reset_index()
    st.bar_chart(grouped.set_index("Stock"))

    st.subheader("Capital Allocation by Trade")
    st.bar_chart(trade_log.set_index("Stock")["Used_Capital"])

    st.subheader("PnL Over Time")
    pnl_time = trade_log.copy()
    pnl_time["Datetime"] = pd.date_range(start=datetime.datetime.now(), periods=len(pnl_time), freq='H')
    st.line_chart(pnl_time.set_index("Datetime")["PnL"])
