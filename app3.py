import streamlit as st
from groq import Groq

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm Dr. Pricing's AI assistant. How can I help with your pricing questions today?"
    }]

# Load API key
try:
    client = Groq(api_key=st.secrets["groq"]["api_key"])
except:
    st.error("Failed to initialize Groq client")
    st.stop()

# Streamlit UI
st.title("💬 Dr. Pricing Assistant")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle user input
if prompt := st.chat_input("Ask about pricing..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        try:
            # Simple direct response without document processing
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are Dr. Pricing, a pricing expert. Answer concisely."},
                    *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                ],
                temperature=0.7
            )
            full_response = response.choices[0].message.content
        except Exception as e:
            full_response = f"Hello! I'm having a temporary issue. Could you ask your pricing question again?"
        
        st.write(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})