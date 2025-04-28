import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- Define Strategy Functions ----------

def strategy_moving_average(df):
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['Signal'] = np.where(df['Close'] > df['SMA20'], 1, -1)
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Close'].pct_change()
    return df, df['Strategy_Return'].cumsum()

def strategy_rsi(df):
    df = df.copy()
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Signal'] = np.where(df['RSI'] < 30, 1, np.where(df['RSI'] > 70, -1, 0))
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Close'].pct_change()
    return df, df['Strategy_Return'].cumsum()

def strategy_bollinger_bands(df):
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['Upper'] = df['SMA20'] + (2 * df['STD20'])
    df['Lower'] = df['SMA20'] - (2 * df['STD20'])
    df['Signal'] = np.where(df['Close'] < df['Lower'], 1, np.where(df['Close'] > df['Upper'], -1, 0))
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Close'].pct_change()
    return df, df['Strategy_Return'].cumsum()

# ---------- Streamlit App Starts Here ----------

st.set_page_config(page_title="Algo Strategy Comparison", layout="wide")

st.title("📈 Algo Trading Strategies Dashboard")

# Sidebar for file upload
st.sidebar.header("Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Assuming CSV has a 'Date' and 'Close' columns
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')

    st.success("✅ File Loaded Successfully!")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Strategy 1 - Moving Average", 
                                            "Strategy 2 - RSI", 
                                            "Strategy 3 - Bollinger Bands",
                                            "Compare All Strategies",
                                            "Raw Data"])

    # ---- Strategy 1 ----
    with tab1:
        st.header("Strategy 1: Moving Average Crossover")
        if st.button("Run Moving Average Strategy"):
            strat1_df, strat1_cumsum = strategy_moving_average(df)
            st.line_chart(strat1_cumsum)
            st.dataframe(strat1_df.tail(10))

    # ---- Strategy 2 ----
    with tab2:
        st.header("Strategy 2: RSI Based Strategy")
        if st.button("Run RSI Strategy"):
            strat2_df, strat2_cumsum = strategy_rsi(df)
            st.line_chart(strat2_cumsum)
            st.dataframe(strat2_df.tail(10))

    # ---- Strategy 3 ----
    with tab3:
        st.header("Strategy 3: Bollinger Bands Breakout")
        if st.button("Run Bollinger Bands Strategy"):
            strat3_df, strat3_cumsum = strategy_bollinger_bands(df)
            st.line_chart(strat3_cumsum)
            st.dataframe(strat3_df.tail(10))

    # ---- Compare All Strategies ----
    with tab4:
        st.header("📊 Compare All Strategies")
        if st.button("Compare Strategies"):
            strat1_df, strat1_cumsum = strategy_moving_average(df)
            strat2_df, strat2_cumsum = strategy_rsi(df)
            strat3_df, strat3_cumsum = strategy_bollinger_bands(df)

            # Plot all strategies together
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(strat1_cumsum, label='Moving Average')
            ax.plot(strat2_cumsum, label='RSI Strategy')
            ax.plot(strat3_cumsum, label='Bollinger Bands')
            ax.set_title('Strategy Cumulative Returns Comparison')
            ax.legend()
            st.pyplot(fig)

            # Show Final Returns
            final_returns = {
                "Strategy": ["Moving Average", "RSI", "Bollinger Bands"],
                "Final Return (%)": [
                    strat1_cumsum.iloc[-1] * 100,
                    strat2_cumsum.iloc[-1] * 100,
                    strat3_cumsum.iloc[-1] * 100
                ]
            }
            final_returns_df = pd.DataFrame(final_returns)
            st.dataframe(final_returns_df)

    # ---- Show Raw Data ----
    with tab5:
        st.header("Raw Uploaded Data")
        st.dataframe(df)

else:
    st.warning("👆 Please upload a CSV file to start.")
