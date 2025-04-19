import streamlit as st
import streamlit.components.v1 as components

# Example: Embedding TradingView widget for NIFTY 50 chart
st.subheader("📊 TradingView NIFTY 50 Chart")

# TradingView Embed Code (replace with the generated embed code from TradingView)
tradingview_embed_code = "
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
  <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
  {
  "autosize": true,
  "symbol": "NASDAQ:AAPL",
  "interval": "D",
  "timezone": "Etc/UTC",
  "theme": "light",
  "style": "1",
  "locale": "en",
  "allow_symbol_change": true,
  "watchlist": [
    "NSEIX:NIFTY1!",
    "NSEIX:BANKNIFTY1!",
    "NSE:BSE"
  ],
  "studies": [
    "STD;Bollinger_Bands",
    "STD;MACD",
    "STD;RSI"
  ],
  "support_host": "https://www.tradingview.com"
}
  </script>
</div>
<!-- TradingView Widget END -->
"

# Display TradingView chart
components.html(tradingview_embed_code, height=900,width=900)
