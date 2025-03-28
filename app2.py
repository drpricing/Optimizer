import streamlit as st

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")
uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Uploaded file: {uploaded_file.name}")
        # You can add more processing logic here

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

# Main module block
if __name__ == "__main__":
    # User input
    if prompt := st.chat_input("Describe your pricing challenge:"):
        st.session_state["conversation"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepend system message to the conversation context for processing
        conversation_context = [
            {"role": "system", "content": "You are Dr. Pricing, a pricing expert as much as a fun person, keeping a low-key profile and avoid using phrases like \"As Dr. Pricing\". Help businesses adjust prices based on market conditions, competitor moves, cost shocks, and demand changes."}
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
