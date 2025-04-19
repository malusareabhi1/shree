import streamlit as st
import pandas as pd
import plotly.express as px

# 📥 Upload trade log file
uploaded_file = st.file_uploader("📘 Upload Trade Log CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.subheader("🧾 Trade Log Table")
    st.dataframe(df)

    # ✅ Show key metrics
    if "PnL" in df.columns:
        total_pnl = df["PnL"].sum()
        win_trades = df[df["PnL"] > 0].shape[0]
        lose_trades = df[df["PnL"] < 0].shape[0]

        st.metric("💰 Net PnL", f"₹{total_pnl:.2f}")
        st.metric("✅ Winning Trades", win_trades)
        st.metric("❌ Losing Trades", lose_trades)

        # 📉 Line chart - PnL over time
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df.sort_values("Date", inplace=True)
            df["Cumulative PnL"] = df["PnL"].cumsum()
            st.subheader("📈 Cumulative PnL Over Time")
            st.line_chart(df.set_index("Date")["Cumulative PnL"])

        # 🥧 Pie chart - Win vs Loss
        st.subheader("📊 Win/Loss Distribution")
        win_loss_df = pd.DataFrame({
            "Result": ["Win", "Loss"],
            "Count": [win_trades, lose_trades]
        })
        fig = px.pie(win_loss_df, names="Result", values="Count", title="Win vs Loss")
        st.plotly_chart(fig, use_container_width=True)

        # 📤 Download button
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Clean Trade Log", csv, "clean_trade_log.csv", "text/csv")
    else:
        st.warning("No 'PnL' column found in CSV.")
else:
    st.info("Upload a CSV file to view trade log.")
