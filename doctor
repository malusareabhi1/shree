import streamlit as st
import pandas as pd
import numpy as np

# --- Doctor Trade Strategy Function ---
def doctor_trade_strategy(df):
    df['Signal'] = 0
    df['MA'] = df['Close'].rolling(window=5).mean()
    df.loc[df['Close'] > df['MA'], 'Signal'] = 1
    df.loc[df['Close'] < df['MA'], 'Signal'] = -1
    df['Position'] = df['Signal'].shift(1)
    df['Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Returns'] * df['Position']
    df['Cumulative Strategy Returns'] = (1 + df['Strategy_Returns'].fillna(0)).cumprod()
    df['Cumulative Market Returns'] = (1 + df['Returns'].fillna(0)).cumprod()
    return df

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("📁 Upload CSV & Run Doctor Trade Strategy")

uploaded_file = st.file_uploader("Upload your stock CSV file", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Attempt to parse date
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

        st.subheader("📊 Raw Data")
        st.dataframe(df.head())

        # Check required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            st.error("CSV must include columns: Open, High, Low, Close, Volume")
        else:
            df = doctor_trade_strategy(df)

            st.subheader("📈 Price Chart")
            st.line_chart(df['Close'])

            st.subheader("🧠 Trade Log")
            trade_log = df[df['Signal'] != 0][['Close', 'Signal']]
            st.dataframe(trade_log.tail(20))

            st.subheader("💰 Strategy vs Market Performance")
            st.line_chart(df[['Cumulative Market Returns', 'Cumulative Strategy Returns']])

            st.success("✅ Strategy Applied Successfully!")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
