import streamlit as st
import groq

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = groq.Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Price Adjustment Advisor")
st.write("Welcome to Dr. Pricing's Price Adjustment Chat! Please describe your pricing challenge below.")

# Create a container for the chat
chat_container = st.container()

# List to keep track of the conversation
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []

# Display previous conversation in the chat container
def display_conversation():
    for message in st.session_state["conversation"]:
        if message["role"] == "user":
            st.markdown(f'<div style="text-align: left; padding: 10px; background-color: #DCF8C6; border-radius: 10px; margin-bottom: 5px;">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align: right; padding: 10px; background-color: #E5E5E5; border-radius: 10px; margin-bottom: 5px;">Dr. Pricing: {message["content"]}</div>', unsafe_allow_html=True)

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
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# User input
user_input = st.text_area("Describe your pricing challenge:", key="input_text")

# Button to get recommendation
if st.button("Send"):
    if user_input.strip():
        # Add user message to conversation
        st.session_state["conversation"].append({"role": "user", "content": user_input})
        
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        
        # Add Dr. Pricing's response to conversation
        st.session_state["conversation"].append({"role": "assistant", "content": advice})

        # Clear input box
        st.session_state.input_text = ""
    else:
        st.warning("Please enter details about your pricing challenge.")

# Display the chat conversation
display_conversation()
