import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ✅ This MUST be the first Streamlit command
#st.set_page_config(page_title="📊 NIFTY 50 Candlestick Chart", layout="wide")

# Now it's safe to use other Streamlit commands
st.title("📈 NIFTY 50 Live Candlestick Chart")
