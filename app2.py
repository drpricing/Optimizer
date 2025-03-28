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

# Dictionary to store uploaded document content
documents_content = {}

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text if text else "No readable text found in PDF."
    except Exception as e:
        logging.error(f"Error reading PDF: {e}")
        return "Error processing PDF file."

# Function to extract text from DOCX
def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        logging.error(f"Error reading DOCX: {e}")
        return "Error processing DOCX file."

# Function to extract text from TXT
def extract_text_from_txt(file):
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        logging.error(f"Error reading TXT: {e}")
        return "Error processing TXT file."

# Function to save file locally
def save_file_locally(uploaded_file):
    os.makedirs("uploaded_files", exist_ok=True)
    file_path = os.path.join("uploaded_files", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Function to upload file to GitHub
def upload_file_to_github(file_path, owner, repo, token):
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{os.path.basename(file_path)}"
    headers = {"Authorization": f"token {token}"}
    
    # Check if file already exists
    response = requests.get(url, headers=headers)
    data = {"message": f"Add {os.path.basename(file_path)}", "content": content}
    if response.status_code == 200:
        data["sha"] = response.json().get("sha")  # Required for updates
    
    response = requests.put(url, headers=headers, json=data)
    if response.status_code in [200, 201]:
        st.success(f"File {os.path.basename(file_path)} uploaded to GitHub successfully!")
    else:
        st.error(f"Error uploading file {os.path.basename(file_path)}: {response.json().get('message', 'Unknown error')}")

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")
uploaded_files = st.file_uploader("Upload files for analysis", accept_multiple_files=True)

# Process uploaded files
if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Processing uploaded file: {uploaded_file.name}")
        
        if uploaded_file.name.endswith(".pdf"):
            file_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            file_text = extract_text_from_docx(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            file_text = extract_text_from_txt(uploaded_file)
        else:
            file_text = uploaded_file.read().decode('utf-8')
        
        # Store extracted text
        documents_content[uploaded_file.name] = file_text
        st.write(f"Extracted text from {uploaded_file.name}: {file_text[:300]}...")  # Show preview

        # Save locally and upload to GitHub
        file_path = save_file_locally(uploaded_file)
        upload_file_to_github(file_path, repo_owner, repo_name, github_token)

# Initialize conversation state
if "conversation" not in st.session_state:
    st.session_state["conversation"] = []
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Function to display conversation
def display_conversation():
    for message in st.session_state["conversation"]:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.write(message["content"])

# Function to search private library
def search_private_library(query):
    results = []
    for path, content in documents_content.items():
        if query.lower() in content.lower():
            results.append(f"🔍 Found in {path}")
    return results if results else ["No relevant information found in uploaded files."]

# Function to call Groq API
def get_pricing_advice(user_input):
    try:
        # Search private library
        library_results = search_private_library(user_input)
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, a pricing expert and enthusiast who speaks clearly and concisely. Your role is to assist businesses as their pricing compass and help individuals understand pricing."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        api_response = response.choices[0].message.get("content", "No response received.")
        
        # Combine responses
        combined_response = api_response + "\n\n" + "\n".join(library_results)
        return combined_response
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return f"Error: {str(e)}"

# Chat input and response handling
if prompt := st.chat_input("Describe your pricing challenge:"):
    st.session_state["conversation"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    response_text = get_pricing_advice(prompt)
    
    with st.chat_message("assistant"):
        st.markdown(response_text)
    
    st.session_state["conversation"].append({"role": "assistant", "content": response_text})
