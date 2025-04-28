import streamlit as st
import pandas as pd
from nsetools import Nse


def generate_signals(df: pd.DataFrame, iv_data: float = 16.0, iv_threshold: float = 16.0) -> pd.DataFrame:
    """
    Given a DataFrame with at least ['Date','Open','High','Low','Close'],
    computes 20-period SMA, Bollinger Bands, and flags BUY signals when:
      1. Reference candle above SMA 20,
      2. Implied volatility ≥ threshold,
      3. Close today > Close yesterday.
    Returns the DataFrame with new columns: ['SMA_20','Upper_BB','Lower_BB',
    'Crossed_SMA_Up','Ref_Candle_Up','Signal'].
    """
    df = df.sort_values('Date').reset_index(drop=True)
    df['SMA_20']   = df['Close'].rolling(window=20).mean()
    df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
    df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()
    df['Crossed_SMA_Up'] = (
        (df['Close'] > df['SMA_20']) &
        (df['Close'].shift(1) < df['SMA_20'].shift(1))
    )
    df['Ref_Candle_Up'] = (
        (df['Close'] > df['SMA_20']) &
        (df['Close'].shift(1) > df['SMA_20'].shift(1))
    )
    df['Signal'] = None
    for idx in range(1, len(df)):
        if df.at[idx, 'Ref_Candle_Up'] and iv_data >= iv_threshold:
            if df.at[idx, 'Close'] > df.at[idx - 1, 'Close']:
                df.at[idx, 'Signal'] = 'BUY'
    return df


def get_live_iv(symbol: str, expiry_date: str, strike_price: float, option_type: str) -> float:
    """
    Fetches live implied volatility from NSE option chain for a given symbol,
    expiry date, strike price, and option type ('CE' or 'PE').
    """
    nse = Nse()
    data = nse.get_stock_option_chain(symbol)
    for rec in data.get('records', {}).get('data', []):
        if rec.get('expiryDate') == expiry_date and rec.get('strikePrice') == strike_price:
            if option_type.upper() == 'CE' and 'CE' in rec:
                return rec['CE'].get('impliedVolatility')
            elif option_type.upper() == 'PE' and 'PE' in rec:
                return rec['PE'].get('impliedVolatility')
    return None


def main():
    st.title("⚙️ Doctor Trade Strategy Signals")
    st.markdown("Upload OHLC CSV and fetch live IV to generate BUY signals.")

    uploaded_file = st.file_uploader("Upload OHLC CSV", type="csv")
    col1, col2 = st.columns(2)
    with col1:
        symbol = st.text_input("Symbol", value="NIFTY")
        expiry = st.text_input("Expiry Date (DD-MMM-YYYY)", value="30-Apr-2025")
    with col2:
        strike = st.number_input("Strike Price", min_value=0.0, value=18000.0)
        opt_type = st.selectbox("Option Type", options=["CE", "PE"], index=0)

    if uploaded_file:
        df = pd.read_csv(uploaded_file, parse_dates=['Date'])
        df = df.sort_values('Date')

        # Fetch live IV
        iv_val = get_live_iv(symbol, expiry, strike, opt_type)
        if iv_val is None:
            st.error("Could not retrieve live IV for given parameters.")
            return
        st.success(f"Live IV for {symbol} {expiry} {strike} {opt_type}: {iv_val:.2f}%")

        # Generate signals
        result_df = generate_signals(df, iv_data=iv_val, iv_threshold=iv_val)
        signals = result_df.dropna(subset=['Signal'])

        if not signals.empty:
            st.subheader("Generated BUY Signals")
            st.dataframe(signals[['Date','Open','High','Low','Close','Signal']])
        else:
            st.info("No BUY signals generated with current IV conditions.")

        # Download all results
        csv_data = result_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Full Signals CSV",
            data=csv_data,
            file_name="doctor_strategy_signals.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
