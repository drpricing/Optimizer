import streamlit as st
from groq import Client
import logging
import uuid
import requests
import base64

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]
github_token = st.secrets["github"]["token"]
repo_owner = "drpricing"
repo_name = "mylibrary"

# List of file paths
file_paths = [
    "2020_Book_ThePricingPuzzle.pdf",
    "2024_Book_ThePricingCompass.pdf",
    "336421_Final proofs.pdf",
    "Book AI-Enabled Pricing_2025.pdf",
    "misc.docx",
    "Simon_Fassnacht-Reference+Document.pdf"
]

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Function to fetch file from GitHub
def get_file_from_github(owner, repo, path, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_content = response.json()["content"]
        try:
            return base64.b64decode(file_content).decode('utf-8')
        except UnicodeDecodeError:
            return base64.b64decode(file_content).decode('latin-1')  # Fallback encoding
    else:
        st.error(f"Error fetching file {path} from GitHub")
        return None

# Load your documents
documents_content = {}
for path in file_paths:
    documents_content[path] = get_file_from_github(repo_owner, repo_name, path, github_token)

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")

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

# Function to extract relevant snippet from a document
def extract_relevant_snippet(content, query, window=200):
    index = content.lower().find(query.lower())
    if index == -1:
        return None
    start = max(0, index - window)
    end = min(len(content), index + len(query) + window)
    return content[start:end] + "..."

# Function to search private library and extract useful information
def search_private_library(query):
    results = []
    for path, content in documents_content.items():
        if content and query.lower() in content.lower():
            snippet = extract_relevant_snippet(content, query)
            if snippet:
                results.append(f"**Source: {path}**\n{snippet}\n")
    return results

# Function to call Groq API with private library context
def get_pricing_advice(user_input):
    try:
        # Search private library
        library_results = search_private_library(user_input)
        library_context = "\n\n".join(library_results) if library_results else "No relevant documents found."

        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, the author of 'The Pricing Puzzle', 'The Pricing Compass', and 'Reimagine Pricing'. You are a pricing expert who speaks clearly and concisely. You help businesses navigate pricing challenges in an engaging manner."},
                {"role": "user", "content": f"User Query: {user_input}\n\nRelevant Information from Private Library:\n{library_context}"}
            ],
            temperature=0.7
        )
        api_response = response.choices[0].message.get("content", "No response received.")

        # Combine responses
        combined_response = api_response
        return combined_response
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return f"Error: {str(e)}"

# Main module block
if __name__ == "__main__":
    # User input
    if prompt := st.chat_input("Describe your pricing challenge:"):
        st.session_state["conversation"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response with library context
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = get_pricing_advice(prompt)
            message_placeholder.markdown(full_response)
            st.session_state["conversation"].append({"role": "assistant", "content": full_response})