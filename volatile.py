import yfinance as yf
import pandas as pd
import streamlit as st

st.title("📈 NIFTY 50 Volatility Scanner (Last 14 Days)")

# Nifty 50 stock symbols (add ".NS" for NSE)
nifty_50 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'LT.NS',
    'SBIN.NS', 'HINDUNILVR.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'BAJFINANCE.NS', 'BHARTIARTL.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'NESTLEIND.NS', 'ULTRACEMCO.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'WIPRO.NS',
    'HCLTECH.NS', 'NTPC.NS', 'POWERGRID.NS', 'ADANIENT.NS', 'TATASTEEL.NS',
    'TECHM.NS', 'COALINDIA.NS', 'ONGC.NS', 'UPL.NS', 'JSWSTEEL.NS',
    'BPCL.NS', 'GRASIM.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'BAJAJFINSV.NS',
    'HDFCLIFE.NS', 'SBILIFE.NS', 'EICHERMOT.NS', 'INDUSINDBK.NS', 'HEROMOTOCO.NS',
    'BAJAJ-AUTO.NS', 'CIPLA.NS', 'BRITANNIA.NS', 'APOLLOHOSP.NS', 'HINDALCO.NS',
    'ADANIPORTS.NS', 'SHREECEM.NS', 'M&M.NS'
]

volatilities = []

with st.spinner("📊 Fetching data and calculating volatility..."):
    for symbol in nifty_50:
        try:
            df = yf.download(symbol, period='15d', interval='1d', progress=False)
            if not df.empty and 'Close' in df.columns:
                df['returns'] = df['Close'].pct_change()
                volatility = df['returns'].std()
                volatilities.append((symbol, volatility))
            else:
                st.warning(f"No data for {symbol}")
        except Exception as e:
            st.exception(f"Error fetching {symbol}: {e}")

if volatilities:
    # Sort by highest volatility
    vol_df = pd.DataFrame(volatilities, columns=['Symbol', 'Volatility'])
    vol_df = vol_df.sort_values(by='Volatility', ascending=False)

    st.subheader("🔍 Top 5 Most Volatile NIFTY 50 Stocks (Last 14 Days)")
    st.dataframe(vol_df.head(5), use_container_width=True)
else:
    st.error("No volatility data could be calculated.")
