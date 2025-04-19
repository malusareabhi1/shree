import streamlit as st

st.title("➕ Add Two Numbers")

# Input fields
num1 = st.number_input("Enter the first number", step=1.0)
num2 = st.number_input("Enter the second number", step=1.0)

# Calculate sum
result = num1 + num2

# Display result
st.success(f"The sum is: {result}")
