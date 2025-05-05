import streamlit as st
import yfinance as yf

st.title("📈 Current NIFTY 50 Price")

# Yahoo Finance symbol for NIFTY 50 index
symbol = "^NSEI"
# Define timeframes
timeframes = {
    "5-Min": {"interval": "5m", "period": "1d"},
    "1-Day": {"interval": "1d", "period": "30d"},
    "1-Week": {"interval": "1wk", "period": "1y"},
    "1-Month": {"interval": "1mo", "period": "5y"},
}
# Function to get current trend
def get_trend(df):
    df["EMA5"] = df["Close"].ewm(span=5, adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()

    if df["EMA5"].iloc[-1] > df["EMA20"].iloc[-1]:
        return "🔼 Uptrend"
    elif df["EMA5"].iloc[-1] < df["EMA20"].iloc[-1]:
        return "🔻 Downtrend"
    else:
        return "➡️ Sideways"

# Separated calculation function
def calculate_trend_for_timeframe(interval, period):
    try:
        df = yf.download(symbol, interval=interval, period=period, progress=False)
        df.dropna(inplace=True)
        trend = get_trend(df)
        current_price = df["Close"].iloc[-1]
        high = df["High"].max()
        low = df["Low"].min()
        return trend, current_price, high, low
    except Exception as e:
        return "Error", 0, 0, 0

try:
    # Fetch intraday data for today
    data = yf.download(symbol, period="1d", interval="1m")

    if data.empty:
        st.error("❌ Failed to fetch NIFTY 50 data.")
    else:
        # Safely get the latest close price as float
        current_price = float(data["Close"].dropna().iloc[-1])
        # Day high
        day_high = float(data["High"].max())
        day_low = float(data["Low"].min())
        trend = get_trend(data)

        # Display metrics
        #st.metric("🔹 Current Price", f"{current_price:.2f} ")
        #st.metric("🔺 Day High", f"{day_high:.2f} ")
        #st.metric("🔻 Day Low", f"{day_low:.2f} ")
        # Display metrics in three columns
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Current Price", f"{current_price:.2f} ₹")
        col2.metric("🔺 Day High", f"{day_high:.2f} ₹")
        col3.metric("🔻 Day Low", f"{day_low:.2f} ₹")
        st.subheader("📊 Trend Analysis")
        st.success(f"Market Trend: {trend}")

       # Display each timeframe trend separately
        for label, tf in timeframes.items():
            st.subheader(f"🕒 {label} Trend")
            trend, price, high, low = calculate_trend_for_timeframe(tf["interval"], tf["period"])
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("📈 Trend", trend)
            col2.metric("💰 Price", f"{price:.2f} ₹")
            col3.metric("🔺 High", f"{high:.2f} ₹")
            col4.metric("🔻 Low", f"{low:.2f} ₹")
            st.divider()




except Exception as e:
    st.error(f"⚠️ Error fetching data: {e}")
