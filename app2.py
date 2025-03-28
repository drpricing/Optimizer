import streamlit as st
from groq import Client
import logging
import uuid
import requests
import base64
import PyPDF2
import docx
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]
github_token = st.secrets["github"]["token"]
repo_owner = "drpricing"
repo_name = "mylibrary"

# Initialize Groq client
client = Client(api_key=groq_api_key)

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")
uploaded_files = st.file_uploader("Upload files for analysis", accept_multiple_files=True)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to save file locally
def save_file_locally(uploaded_file):
    os.makedirs("uploaded_files", exist_ok=True)  # Ensure the directory exists
    file_path = os.path.join("uploaded_files", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Handle uploaded files and extract content
documents_content = {}
if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Processing file: {uploaded_file.name}")
        
        # Extract text based on file type
        if uploaded_file.name.endswith(".pdf"):
            file_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            file_text = extract_text_from_docx(uploaded_file)
        else:
            file_text = uploaded_file.read().decode('utf-8')
        
        # Store the content for future use
        documents_content[uploaded_file.name] = file_text
        
        # Save file locally (optional for GitHub upload)
        file_path = save_file_locally(uploaded_file)

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
        # Search private library (documents_content contains the text of the uploaded files)
        library_results = [f"Found in {path}: {content[:500]}" for path, content in documents_content.items() if user_input.lower() in content.lower()]
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": "You are Dr. Pricing, a pricing expert."},
                      {"role": "user", "content": user_input}]
        )
        
        # Combine responses
        api_response = response.choices[0].message["content"] if response.choices else "No response received."
        combined_response = api_response + "\n\n" + "\n".join(library_results)
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
        
        # Prepend system message to the conversation context for processing
        conversation_context = [{"role": "system", "content": "You are Dr. Pricing, a pricing expert."}] + st.session_state["conversation"]
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model="llama3-70b-8192", messages=conversation_context, stream=True
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state["conversation"].append({"role": "assistant", "content": full_response})
