import streamlit as st
from groq import Client

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Pricing Advisor")
st.write("Welcome to Dr. Pricing's Pricing Chat! Please describe your pricing challenge below.")

# Initialize session state for conversation
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Function to display conversation
def display_conversation():
    for message in st.session_state["conversation"]:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.write(message["content"])

# Function to call Groq API
def get_pricing_advice(user
