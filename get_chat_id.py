import requests
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_demo")

bot_token = os.getenv("TELEGRAM_BOT_TOKEN_demo")
#st.write(bot_token)


st.title("🔍 Telegram Bot Chat ID Finder")

# Input token manually or load from .env
#bot_token = st.text_input("Enter your Telegram Bot Token:", value=os.getenv("TELEGRAM_BOT_TOKEN", ""), type="password")

if st.button("Fetch Chat ID"):
    if not bot_token:
        st.error("Please enter a valid bot token.")
    else:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
            response = requests.get(url)
            data = response.json()

            if not data["result"]:
                st.warning("No recent messages found. Send a message to your bot or group and try again.")
            else:
                for result in data["result"]:
                    message = result.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    chat_type = chat.get("type")
                    title = chat.get("title") or chat.get("username")

                    st.success(f"✅ Found Chat:\n\n"
                               f"**Chat ID**: `{chat_id}`\n"
                               f"**Type**: `{chat_type}`\n"
                               f"**Title/User**: `{title}`")

        except Exception as e:
            st.error(f"Error fetching updates: {e}")

    
 
