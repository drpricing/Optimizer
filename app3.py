import streamlit as st
from groq import Groq

# Initialize session state if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm Dr. Pricing's AI assistant. How can I help with your pricing questions today?"
    }]

# Load API key and initialize the Groq client
try:
    api_key = st.secrets["groq"]["api_key"]
    client = Groq(api_key=api_key)
except Exception as err:
    st.error(f"Failed to initialize Groq client: {err}")
    st.stop()

# Set up the Streamlit UI
st.title("💬 Dr. Pricing Assistant")

# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle user input
user_input = st.chat_input("Ask about pricing...")
if user_input:
    # Add the user message to the session state and display it
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # Prepare the payload for the Groq API, including a system prompt and the chat history
    messages_payload = [
        {"role": "system", "content": "You are Dr. Pricing, a pricing expert. Answer concisely."}
    ] + st.session_state.messages

    # Attempt to get the assistant response from the Groq API
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages_payload,
            temperature=0.7
        )
        # Optionally, display the full response object for debugging:
        # st.write("Full API response:", response)
        full_response = response.choices[0].message.content
    except Exception as e:
        st.error(f"Error during API call: {e}")
        full_response = "Hello! I'm having a temporary issue. Could you ask your pricing question again?"

    # Display and store the assistant's response
    with st.chat_message("assistant"):
        st.write(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})