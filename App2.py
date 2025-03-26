import streamlit as st
from groq import Client
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Price Adjustment Advisor")
st.write("Welcome to Dr. Pricing's Price Adjustment Chat! Please describe your pricing challenge below.")

# Initialize session state for conversation and other variables
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Function to display conversation
def display_conversation():
    for message in st.session_state["conversation"]:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.write(message["content"])

# Function to call Groq API
def get_pricing_advice(user_input):
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, a pricing strategy expert. Help businesses adjust prices based on market conditions, competitor moves, cost shocks, and demand changes."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        return response.choices[0].message.get("content", "No response received.")
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return f"Error: {str(e)}"

# User input
if prompt := st.chat_input("Describe your pricing challenge:"):
    st.session_state["conversation"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Prepend system message to the conversation context for processing
    conversation_context = [
        {"role": "system", "content": "You are Dr. Pricing, a pricing strategy expert. Help businesses adjust prices based on market conditions, competitor moves, cost shocks, and demand changes."}
    ] + st.session_state["conversation"]
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        for response in client.chat.completions.create(
            model="llama3-70b-8192",
            messages=conversation_context,
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        st.session_state["conversation"].append({"role": "assistant", "content": full_response})

# Display conversation
display_conversation()
