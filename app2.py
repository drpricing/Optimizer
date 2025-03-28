import streamlit as st
import logging
import uuid
import requests
import base64
import PyPDF2
import docx
import os
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API keys and repository details from Streamlit secrets
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
            return base64.b64decode(file_content).decode('latin-1')  # Fallback to another encoding
    else:
        st.error(f"Error fetching file {path} from GitHub")
        return None

# Load documents from GitHub
documents_content = {}
for path in file_paths:
    documents_content[path] = get_file_from_github(repo_owner, repo_name, path, github_token)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

# Function to extract text from DOCX
def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        logging.error(f"Error extracting text from DOCX: {e}")
        return ""

# Function to extract text from TXT
def extract_text_from_txt(file):
    try:
        return file.read().decode('utf-8')
    except Exception as e:
        logging.error(f"Error extracting text from TXT: {e}")
        return ""

# Function to save file locally
def save_file_locally(uploaded_file):
    os.makedirs("uploaded_files", exist_ok=True)  # Ensure the directory exists
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
    try:
        file_exists, sha = check_file_exists_on_github(file_path, owner, repo, token)
        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{os.path.basename(file_path)}"
        headers = {"Authorization": f"token {token}"}
        data = {
            "message": f"Add {os.path.basename(file_path)}",
            "content": content
        }
        if file_exists:
            data["sha"] = sha
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 201 or response.status_code == 200:
            st.success(f"File {os.path.basename(file_path)} uploaded to GitHub successfully!")
        else:
            st.error(f"Error uploading file {os.path.basename(file_path)} to GitHub: {response.json().get('message', 'Unknown error')}")
    except Exception as e:
        logging.error(f"Error uploading file to GitHub: {e}")
        st.error(f"Error uploading file to GitHub: {e}")

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")
uploaded_files = st.file_uploader("Upload files for analysis", accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"Processing file: {uploaded_file.name}")
        if uploaded_file.name.endswith(".pdf"):
            file_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.name.endswith(".docx"):
            file_text = extract_text_from_docx(uploaded_file)
        elif uploaded_file.name.endswith(".txt"):
            file_text = extract_text_from_txt(uploaded_file)
        else:
            file_text = uploaded_file.read().decode('utf-8')
        
        documents_content[uploaded_file.name] = file_text
        
        # Save file locally and upload to GitHub
        file_path = save_file_locally(uploaded_file)
        upload_file_to_github(file_path, repo_owner, repo_name, github_token)

# Initialize session state for conversation and other variables
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Function to get response from Groq AI
def get_groq_response(prompt):
    try:
        response = client.chat(prompt)
        return response.get("choices", [{}])[0].get("message
::contentReference[oaicite:9]{index=9}
 
