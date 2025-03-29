import streamlit as st
from groq import Groq
import requests
import base64

# --- Private Library Configuration ---
github_token = st.secrets["github"]["token"]
repo_owner = "drpricing"
repo_name = "mylibrary"

# List of file paths in the private repository
file_paths = [
    "2020_Book_ThePricingPuzzle.pdf",
    "2024_Book_ThePricingCompass.pdf",
    "336421_Final proofs.pdf",
    "Book AI-Enabled Pricing_2025.pdf",
    "misc.docx",
    "Simon_Fassnacht-Reference+Document.pdf"
]

def fetch_file_content(path):
    """
    Fetch the file content from a private GitHub repository.
    Returns decoded text if the file is base64-encoded; otherwise None.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    headers = {"Authorization": f"token {github_token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Check if content is base64 encoded
        if data.get("encoding") == "base64":
            try:
                content = base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
                return content
            except Exception as e:
                st.error(f"Error decoding content from {path}: {e}")
    else:
        st.error(f"Failed to fetch {path} from GitHub (status code: {response.status_code})")
    return None

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm Dr. Pricing's AI assistant. How can I help with your pricing questions today?"
    }]

# --- Initialize the Groq Client ---
try:
    api_key = st.secrets["groq"]["api_key"]
    client = Groq(api_key=api_key)
except Exception as err:
    st.error(f"Failed to initialize Groq client: {err}")
    st.stop()

# --- Streamlit UI Setup ---
st.title("💬 Dr. Pricing Assistant")

# Display the chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- Handle User Input ---
user_input = st.chat_input("Ask about pricing...")
if user_input:
    # Append and display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # --- Fetch Relevant Information from Private Library ---
    library_context = ""
    for path in file_paths:
        file_content = fetch_file_content(path)
        if file_content and user_input.lower() in file_content.lower():
            # Extract a snippet (e.g., first 500 characters) for context
            snippet = file_content[:500]
            library_context += f"From {path}:\n{snippet}\n\n"
    
    # --- Construct the Payload ---
    # Start with a system message for behavior
    messages_payload = [
        {"role": "system", "content": "You are Dr. Pricing, a pricing expert. Answer concisely."}
    ]
    
    # If any relevant library info was found, add it as additional context.
    if library_context:
        messages_payload.append({
            "role": "system",
            "content": f"Additional context from private library:\n{library_context}"
        })
    
    # Append the chat history (user and assistant messages)
    messages_payload.extend(st.session_state.messages)
    
    # --- Query the Groq API ---
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages_payload,
            temperature=0.7
        )
        full_response = response.choices[0].message.content
    except Exception as e:
        st.error(f"Error during API call: {e}")
        full_response = "Hello! I'm having a temporary issue. Could you ask your pricing question again?"
    
    # Display and store the assistant's response
    with st.chat_message("assistant"):
        st.write(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})