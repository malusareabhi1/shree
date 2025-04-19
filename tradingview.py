import streamlit as st
import streamlit.components.v1 as components

st.subheader("📈 Live NIFTY 50 Chart")

tradingview_chart = """
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <iframe src="https://www.tradingview.com/chart/?symbol=NSE:NIFTY" width="100%" height="500" frameborder="0" allowfullscreen></iframe>
</div>
<!-- TradingView Widget END -->
"""

components.html(tradingview_chart, height=500)

symbol_map = {
    "NIFTY 50": "NSE:NIFTY",
    "BANK NIFTY": "NSE:BANKNIFTY",
    "SENSEX (BSE)": "BSE:SENSEX",
    "RELIANCE": "NSE:RELIANCE"
}

selected_symbol = st.selectbox("📌 Select Market/Stock", options=list(symbol_map.keys()))
chart_url = f"https://www.tradingview.com/chart/?symbol={symbol_map[selected_symbol]}"

components.html(f"<iframe src='{chart_url}' width='100%' height='500' frameborder='0'></iframe>", height=500)
