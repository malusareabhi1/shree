import streamlit as st
import streamlit.components.v1 as components

st.subheader("📈 Live NIFTY Chart")

# Correctly wrap HTML iframe in triple quotes
tradingview_chart = """
<iframe 
    src="https://www.tradingview.com/widgetembed/?frameElementId=tradingview_live&symbol=NSE%3ANIFTY&interval=1&theme=dark&style=1&locale=en"
    width="100%" 
    height="500" 
    frameborder="0" 
    allowtransparency="true" 
    scrolling="no"
    allowfullscreen>
</iframe>
"""

# Display in Streamlit
components.html(tradingview_chart, height=500)

symbol_map = {
    "NIFTY 50": "NSE:NIFTY",
    "BANK NIFTY": "NSE:BANKNIFTY",
    "SENSEX (BSE)": "BSE:SENSEX",
    "RELIANCE": "NSE:RELIANCE"
}

selected_symbol = st.selectbox("📌 Select Market/Stock", options=list(symbol_map.keys()))
#chart_url = f"https://www.tradingview.com/chart/?symbol={symbol_map[selected_symbol]}"
chart_url = f"https://www.tradingview.com/widgetembed/?frameElementId=tradingview_live&symbol={symbol_map[selected_symbol]}&theme=dark&style=1&locale=en"

components.html(f"<iframe src='{chart_url}' width='100%' height='500' frameborder='0'></iframe>", height=500)

