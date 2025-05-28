import streamlit as st

# Main menu
main_menu = st.sidebar.selectbox("Main Menu", ["Dashboard", "Trading", "Settings"])

# Submenu based on main menu
if main_menu == "Dashboard":
    submenu = st.sidebar.radio("Dashboard Options", ["Overview", "Performance"])
    if submenu == "Overview":
        st.title("📈 Overview")
    elif submenu == "Performance":
        st.title("📉 Performance")

elif main_menu == "Trading":
    submenu = st.sidebar.radio("Trading Options", ["Backtest", "Live"])
    if submenu == "Backtest":
        st.title("🔁 Backtest")
    elif submenu == "Live":
        st.title("📡 Live Trading")

elif main_menu == "Settings":
    st.title("⚙️ Settings")
    st.write("Update config, alerts, and preferences.")
