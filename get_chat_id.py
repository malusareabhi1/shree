import requests
from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_demo")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_demo")
st.write(BOT_TOKEN)
# Get updates from Telegram API
url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(url)
data = response.json()

# Print all messages and chat IDs
for result in data["result"]:
    message = result.get("message", {})
    chat = message.get("chat", {})
    st.write(chat)
   # st.write(f"Chat ID: {chat.get('id')} | Chat Type: {chat.get('type')} | Title: {chat.get('title')}")
    
 
