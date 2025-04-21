import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="📈 Candlestick Chart with Date Range", layout="wide")
st.title("📊 Candlestick Chart Viewer")

# 1) Stock symbol input
stock_symbol = st.text_input("Enter Stock Symbol (e.g., NIFTY, AAPL, TSLA):", "NIFTY")

# 2) Date range selectors
col1, col2 = st.columns(2)
with col1:
    from_date = st.date_input("From Date", datetime.today() - timedelta(days=30))
with col2:
    to_date = st.date_input("To Date", datetime.today())

# 3) Interval selector
interval = st.selectbox("Interval", ["1m","5m","15m","30m","1h","1d"], index=1)

# 4) Fetch data button
if st.button("🔄 Fetch & Plot"):
    if from_date >= to_date:
        st.error("⚠️ ‘From Date’ must be before ‘To Date’")
    else:
        st.write(f"Fetching {stock_symbol} from {from_date} to {to_date} @ {interval} interval…")
        # yfinance end date is exclusive, so add one day to include to_date
        df = yf.download(
            tickers=stock_symbol,
            start=from_date,
            end=to_date + timedelta(days=1),
            interval=interval,
            progress=False
        )

        if df.empty:
            st.warning("No data found for that range. Try adjusting dates or symbol.")
        else:
            # Show last few rows
            st.subheader("📝 Data Preview")
            st.write(df.tail())

            # Plot candlestick
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])
            fig.update_layout(
                title=f"{stock_symbol} Candlestick ({from_date} → {to_date})",
                xaxis_title="Time",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False,
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
