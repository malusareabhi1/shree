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
