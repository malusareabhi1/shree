import streamlit as st
import requests

# --- Configuration ---
st.title("📤 Telegram Bot Messenger")

bot_token = st.text_input("Enter your Telegram Bot Token", type="password")
chat_id = st.text_input("Enter your Telegram Chat ID")

message = st.text_area("Enter the message to send")

if st.button("Send to Telegram"):
    if bot_token and chat_id and message:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            st.success("✅ Message sent successfully!")
        else:
            st.error(f"❌ Failed to send message. Status code: {response.status_code}")
            st.json(response.json())
    else:
        st.warning("⚠️ Please enter bot token, chat ID, and a message.")
