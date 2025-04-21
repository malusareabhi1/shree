import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="📈 Candlestick Chart with Date Range", layout="wide")
st.title("📊 Candlestick Chart Viewer")

uploaded_file = st.file_uploader("Upload CSV file with Date, Open, High, Low, Close columns", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, parse_dates=["Date"])
    df.columns = df.columns.str.strip()

    required_cols = {"Date", "Open", "High", "Low", "Close"}
    if not required_cols.issubset(df.columns):
        st.error(f"CSV must contain columns: {required_cols}")
    else:
        # Sort and set index
        df = df.sort_values("Date")
        df = df.set_index("Date")

        # Select date range
        min_date = df.index.min().date()
        max_date = df.index.max().date()

        st.sidebar.subheader("📅 Select Date Range")
        from_date = st.sidebar.date_input("From Date", min_value=min_date, max_value=max_date, value=min_date)
        to_date = st.sidebar.date_input("To Date", min_value=min_date, max_value=max_date, value=max_date)

        if from_date > to_date:
            st.error("❌ 'From Date' cannot be after 'To Date'")
        else:
            filtered_df = df.loc[str(from_date):str(to_date)]

            if filtered_df.empty:
                st.warning("No data in the selected date range.")
            else:
                st.subheader("📝 Data Preview")
                st.dataframe(filtered_df.tail())

                # Plot candlestick chart
                fig = go.Figure(data=[go.Candlestick(
                    x=filtered_df.index,
                    open=filtered_df['Open'],
                    high=filtered_df['High'],
                    low=filtered_df['Low'],
                    close=filtered_df['Close'],
                    increasing_line_color='green',
                    decreasing_line_color='red'
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
