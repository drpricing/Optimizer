import streamlit as st

class SessionState:
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

def get_session_state(**kwargs):
    session_state = st.session_state.get('_session_state', None)
    if session_state is None:
        session_state = SessionState(**kwargs)
        st.session_state['_session_state'] = session_state
    return session_state

# Initialize session state
session_state = get_session_state(conversation=[], input_text="")

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Price Adjustment Advisor")
st.write("Welcome to Dr. Pricing's Price Adjustment Chat! Please describe your pricing challenge below.")

# Function to display conversation
def display_conversation():
    for message in session_state.conversation:
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

# User input
user_input = st.text_area("Describe your pricing challenge:", key="input_text")

# Button to get recommendation
if st.button("Send"):
    if user_input.strip():
        # Add user message to conversation
        session_state.conversation.append({"role": "user", "content": user_input})
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        # Add Dr. Pricing's response to conversation
        session_state.conversation.append({"role": "assistant", "content": advice})
        # Clear input field safely
        session_state.input_text = ""
    else:
        st.warning("Please enter details about your pricing challenge.")

# Display conversation
display_conversation()
