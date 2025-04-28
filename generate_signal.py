import streamlit as st
import pandas as pd
from kiteconnect import KiteConnect
import math
from scipy.stats import norm

# ----- Utility Functions -----

def calculate_implied_volatility(S, K, T, r, market_price, option_type="CE"):
    """
    Calculate implied volatility using the Black-Scholes model via Newton-Raphson.
    """
    def bs_price(sigma):
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        if option_type == "CE":
            return S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:
            return K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    sigma = 0.2
    for _ in range(100):
        price = bs_price(sigma)
        # Vega
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        vega = S * norm.pdf(d1) * math.sqrt(T)
        sigma -= (price - market_price) / vega
        if abs(price - market_price) < 1e-3:
            break
    return sigma


def generate_signals(df: pd.DataFrame, iv_data: float, iv_threshold: float) -> pd.DataFrame:
    df = df.sort_values('Date').reset_index(drop=True)
    df['SMA_20']   = df['Close'].rolling(20).mean()
    df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(20).std()
    df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(20).std()
    df['Ref_Candle_Up'] = (
        (df['Close'] > df['SMA_20']) &
        (df['Close'].shift(1) > df['SMA_20'].shift(1))
    )
    df['Signal'] = None
    for i in range(1, len(df)):
        if df.at[i, 'Ref_Candle_Up'] and iv_data >= iv_threshold:
            if df.at[i, 'Close'] > df.at[i - 1, 'Close']:
                df.at[i, 'Signal'] = 'BUY'
    return df


def get_live_iv_kite(kite: KiteConnect, symbol: str, expiry: str, strike: float, opt_type: str):
    """
    Fetch option LTP via Kite, then compute IV via Black-Scholes.
    expiry format: 'DDMMMYYYY', e.g. '30APR2025'
    """
    try:
        option_token = f"{symbol}{expiry}{int(strike)}{opt_type}"
        ltp_data = kite.ltp([f"NSE:{option_token}"])
        opt_price = ltp_data[f"NSE:{option_token}"]['last_price']
        # Get underlying price
        underlying_data = kite.ltp([f"NSE:{symbol}50"])
        S = underlying_data[f"NSE:{symbol}50"]['last_price']
        # Assume r and T
        r = 0.05
        # compute days to expiry
        from datetime import datetime
        expiry_dt = datetime.strptime(expiry, "%d%b%Y")
        T = (expiry_dt - datetime.now()).days / 365
        iv = calculate_implied_volatility(S, strike, T, r, opt_price, opt_type)
        return iv * 100  # in percent
    except Exception as e:
        st.error(f"Error fetching IV: {e}")
        return None


# ----- Streamlit App -----

def main():
    st.sidebar.title("Navigation")
    choice = st.sidebar.selectbox("Go to", ["Doctor Strategy", "KITE API"])

    if choice == "Doctor Strategy":
        st.header("⚙️ Doctor Strategy Signal Generator")
        file = st.file_uploader("Upload OHLC CSV", type='csv')
        iv_thresh = st.number_input("IV Threshold (%)", value=16.0, step=0.1)
        if file:
            df = pd.read_csv(file, parse_dates=['Date'])
            iv_val = st.number_input("Use IV Value (%)", value=iv_thresh)
            signals_df = generate_signals(df, iv_val, iv_thresh)
            signals = signals_df.dropna(subset=['Signal'])
            st.dataframe(signals[['Date','Close','Signal']])

    else:
        st.header("🔐 Kite Connect API (Zerodha)")
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")
        if api_key and api_secret:
            kite = KiteConnect(api_key=api_key)
            login_url = kite.login_url()
            st.markdown(f"[Login to Zerodha]({login_url})")
            token = st.text_input("Request Token")
            if token:
                data = kite.generate_session(token, api_secret)
                kite.set_access_token(data['access_token'])
                st.success("Logged in to Kite API")
                # IV Fetch Controls
                st.subheader("Fetch Live Implied Volatility")
                symbol = st.text_input("Symbol", value="NIFTY")
                expiry = st.text_input("Expiry (DDMONYYYY)", value="30APR2025")
                strike = st.number_input("Strike Price", value=18000.0)
                opt_type = st.selectbox("Option Type", ["CE","PE"])
                if st.button("Get Live IV"):
                    iv = get_live_iv_kite(kite, symbol, expiry, strike, opt_type)
                    if iv is not None:
                        st.success(f"Implied Volatility: {iv:.2f}%")
                        # Optionally: load OHLC for signals
                        if st.checkbox("Generate Signals using this IV"):
                            file = st.file_uploader("Upload OHLC CSV for Signals", type='csv')
                            if file:
                                df = pd.read_csv(file, parse_dates=['Date'])
                                df = df.sort_values('Date')
                                res = generate_signals(df, iv, iv)
                                sig = res.dropna(subset=['Signal'])
                                st.dataframe(sig[['Date','Close','Signal']])

if __name__ == "__main__":
    main()
