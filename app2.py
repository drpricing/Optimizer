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

# Load API keys from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]
github_token = st.secrets["github"]["token"]
repo_owner = "drpricing"
repo_name = "mylibrary"

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
        return None  # Return None instead of showing error inside function

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = "".join([page.extract_text() or "" for page in reader.pages])
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to extract text from TXT
def extract_text_from_txt(file):
    return file.read().decode('utf-8')

# Function to save file locally
def save_file_locally(uploaded_file):
    os.makedirs("uploaded_files", exist_ok=True)  # Ensure directory exists
    file_path = os.path.join("uploaded_files", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Function to check if file exists on GitHub
def check_file_exists_on_github(file_path, owner, repo, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{os.path.basename(file_path)}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200, response.json().get("sha")

# Function to upload file to GitHub
def upload_file_to_github(file_path, owner, repo, token):
    file_exists, sha = check_file_exists_on_github(file_path, owner, repo, token)
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{os.path.basename(file_path)}"
    headers = {"Authorization": f"token {token}"}
    data = {"message": f"Add {os.path.basename(file_path)}", "content": content}
    if file_exists:
        data["sha"] = sha
    response = requests.put(url, headers=headers, json=data)
    return response.status_code in (200, 201)

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")
uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)

# Store file contents
documents_content = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Uploaded file: {uploaded_file.name}")
        if uploaded_file.name.endswith(".pdf"):
            file_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            file_text = extract_text_from_docx(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            file_text = extract_text_from_txt(uploaded_file)
        else:
            file_text = uploaded_file.read().decode('utf-8', errors="ignore")
        
        documents_content[uploaded_file.name] = file_text
        
        # Save file locally and upload to GitHub
        file_path = save_file_locally(uploaded_file)
        success = upload_file_to_github(file_path, repo_owner, repo_name, github_token)
        if success:
            st.success(f"File {uploaded_file.name} uploaded to GitHub!")
        else:
            st.error(f"Failed to upload {uploaded_file.name} to GitHub.")

# Initialize session state
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
            results.append(f"Found in {path}")
    return results

# Function to call Groq API
def get_pricing_advice(user_input):
    try:
        library_results = search_private_library(user_input)
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, an expert pricing consultant. You provide clear, engaging, and concise advice to businesses on pricing strategies."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        api_response = response.choices[0].message.content
        
        return api_response + "\n\n" + "\n".join(library_results)
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return f"Error: {str(e)}"

# User Input
if prompt := st.chat_input("Describe your pricing challenge:"):
    st.session_state["conversation"].append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process input and display response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            for response in client.chat.completions.create(
                model="llama3-70b-8192",
                messages=st.session_state["conversation"],
                stream=True
            ):
                chunk = response.choices[0].delta.content or ""
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            st.session_state["conversation"].append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"Error processing request: {e}")
            logging.error(f"Streaming Error: {e}")
