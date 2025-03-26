import streamlit as st
from groq import Client

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Price Adjustment Advisor")
st.write("Welcome to Dr. Pricing's Price Adjustment Chat! Please describe your pricing challenge below.")

# Initialize session state for conversation
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Ensure input_text is initialized in session state
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

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
        return f"Error: {str(e)}"

# Callback function to clear input_text
def clear_input():
    st.session_state["input_text"] = ""

# User input
user_input = st.text_area("Describe your pricing challenge:", key="input_text")

# Button to get recommendation
if st.button("Send", on_click=clear_input):
    if user_input.strip():
        # Add user message to conversation
        st.session_state["conversation"].append({"role": "user", "content": user_input})
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        # Add Dr. Pricing's response to conversation
        st.session_state["conversation"].append({"role": "assistant", "content": advice})
    else:
        st.warning("Please enter details about your pricing challenge.")

# Display conversation
display_conversation()
3. Debugging and Logging
Add logging to your code to help identify where the issue is occurring. This can provide more insight into the problem.

import streamlit as st
from groq import Client
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Price Adjustment Advisor")
st.write("Welcome to Dr. Pricing's Price Adjustment Chat! Please describe your pricing challenge below.")

# Initialize session state for conversation
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Ensure input_text is initialized in session state
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

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

# Callback function to clear input_text
def clear_input():
    st.session_state["input_text"] = ""

# User input
user_input = st.text_area("Describe your pricing challenge:", key="input_text")

# Button to get recommendation
if st.button("Send", on_click=clear_input):
    if user_input.strip():
        # Add user message to conversation
        st.session_state["conversation"].append({"role": "user", "content": user_input})
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        # Add Dr. Pricing's response to conversation
        st.session_state["conversation"].append({"role": "assistant", "content": advice})
    else:
        st.warning("Please enter details about your pricing challenge.")

# Display conversation
display_conversation()
These steps should help identify and resolve the root cause of the StreamlitAPIException. Let me know if you need further assistance!



Favicon type
State Management best practices - Using Streamlit - Streamlit

Favicon type
Session State - Streamlit Docs

Favicon type
Seeking Advice for Streamlit App State Management and Best Practices
Show more

Edit in Pages





AI-generated content may be incorrect
You said:

pls finalize the code for me
Copilot said:
Copilot
Sure, let's finalize the code to ensure it handles the session state properly and avoids the StreamlitAPIException. Here is the complete and corrected version of your Streamlit app:

import streamlit as st
from groq import Client
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Price Adjustment Advisor")
st.write("Welcome to Dr. Pricing's Price Adjustment Chat! Please describe your pricing challenge below.")

# Initialize session state for conversation
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Ensure input_text is initialized in session state
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

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

# Callback function to clear input_text
def clear_input():
    st.session_state["input_text"] = ""

# User input
user_input = st.text_area("Describe your pricing challenge:", key="input_text")

# Button to get recommendation
if st.button("Send", on_click=clear_input):
    if user_input.strip():
        # Add user message to conversation
        st.session_state["conversation"].append({"role": "user", "content": user_input})
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        # Add Dr. Pricing's response to conversation
        st.session_state["conversation"].append({"role": "assistant", "content": advice})
    else:
        st.warning("Please enter details about your pricing challenge.")

# Display conversation
display_conversation()
