import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

    st.set_page_config(page_title="📈 Candlestick Chart with Date Range", layout="wide")
    st.title("📊 Candlestick Chart Viewer")
    
    uploaded_file = st.file_uploader("Upload CSV file with Date, Open, High, Low, Close columns", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, parse_dates=["Date"])
        df.columns = df.columns.str.strip()
        required_cols = {"Date","Open","High","Low","Close"}
        if not required_cols.issubset(df.columns):
            st.error(f"CSV must contain columns: {required_cols}")
        else:
            # Prepare DataFrame
            df = df.sort_values("Date")
            df = df.set_index("Date")
            # Filter by date range
            df = df.loc[from_date: to_date]
            if df.empty:
                st.warning("No data in the selected date range.")
            else:
                st.subheader("📝 Data Preview")
                st.dataframe(df.tail())

                # Plot candlestick chart
                import plotly.graph_objects as go
                fig = go.Figure(data=[go.Candlestick(
                    x=df.index,
                    open=df['Open'], high=df['High'],
                    low=df['Low'], close=df['Close'],
                    increasing_line_color='green', decreasing_line_color='red'
                )])
                fig.update_layout(
                    title="Candlestick Chart (from file)",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    xaxis_rangeslider_visible=False,
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Please upload a CSV file to view the chart.")

   
