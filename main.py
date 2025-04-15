import streamlit as st

st.title("👋 Hello, Streamlit!")

st.write("This is your first Streamlit app.")
st.write("Streamlit makes it easy to build web apps with Python!")

name = st.text_input("What's your name?")
if name:
    st.success(f"Nice to meet you, {name}!")
