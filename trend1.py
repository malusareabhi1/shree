import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# Fetch live NIFTY data for the last 7 days
symbol = "^NSEBANK"  # NIFTY Bank symbol
df = yf.download(symbol, period="7d", interval="1d")

# Check if data is loaded
if df.empty:
    st.error("❌ Failed to load NIFTY data.")
else:
    # Display raw data for debugging
    st.write(df.tail())

    # Candlestick chart
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                        open=df['Open'],
                                        high=df['High'],
                                        low=df['Low'],
                                        close=df['Close'],
                                        name='Candlestick')])

    # Customize layout
    fig.update_layout(
        title="NIFTY Daily Candlestick Chart",
        xaxis_title="Date",
        yaxis_title="Price (INR)",
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig)
    
