import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.trend import EMAIndicator
st.set_page_config(layout="wide")
st.title("📈 Intraday Opening Range Breakout Strategy")

# User input
symbol = st.text_input("Enter NSE Stock Symbol (e.g., RELIANCE.NS)", "RELIANCE.NS")
