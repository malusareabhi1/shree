import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ✅ Page config MUST be the FIRST Streamlit command
st.set_page_config(page_title="📊 NIFTY 50 Candlestick Chart", layout="wide")

# 🧾 Title
st.title("📈 NIFTY 50 Live Candlestick Chart (1-min)")

# 📥 Fetch Nifty data
ticker = "^NSEI"
nifty = yf.Ticker(ticker)
data = nifty.history(period="1d", interval="1m")

if not data.empty:
    # 🕯️ Candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        increasing_line_color='green',
        decreasing_line_color='red'
    )])

    fig.update_layout(
        title="NIFTY 50 - Live Candlestick (1 Minute)",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # 💰 Live price metric
    latest_price = data["Close"].iloc[-1]
    st.metric("Live Price", f"{latest_price:.2f}")
else:
    st.error("⚠️ Unable to fetch NIFTY 50 data.")
