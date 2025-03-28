import streamlit as st
from groq import Client
import logging
import uuid
import requests
import base64
import PyPDF2
import docx

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
            return base64.b64decode(file_content).decode('latin-1')  # Fallback to another encoding
    else:
        st.error(f"Error fetching file {path} from GitHub")
        return None

# Load your documents
documents_content = {}
for path in file_paths:
    documents_content[path] = get_file_from_github(repo_owner, repo_name, path, github_token)

# Function to extract text from PDF
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfFileReader(file)
    text = ""
    for page_num in range(reader.numPages):
        page = reader.getPage(page_num)
        text += page.extract_text()
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Function to extract text from TXT
def extract_text_from_txt(file):
    return file.read().decode('utf-8')

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.write("Welcome to Dr. Pricing's ChatBot! Please describe your pricing challenge below. Enjoy while it lasts! (:")
uploaded_files = st.file_uploader("Upload files for analysis", accept_multiple_files=True)

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
            file_text = uploaded_file.read().decode('utf-8')
        documents_content[uploaded_file.name] = file_text

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
        # Search private library
        library_results = search_private_library(user_input)
        
        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, a pricing expert and enthusiast as much as a fun person, known for speaking in a clear and concise fashion, talking like a real human-being with a low-key profile and avoiding using phrases like \"As Dr. Pricing\". Assist businesses as their pricing compass. Help individuals understand and appreciate how pricing works, resolving their pricing puzzles."},
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

# Main module block
if __name__ == "__main__":
    # User input
    if prompt := st.chat_input("Describe your pricing challenge:"):
        st.session_state["conversation"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Prepend system message to the conversation context for processing
        conversation_context = [
            {"role": "system", "content": "You are Dr. Pricing, a pricing expert and enthusiast as much as a fun person, known for speaking in a clear and concise fashion, talking like a real human-being with a low-key profile and avoiding using phrases like \"As Dr. Pricing\". Assist businesses as their pricing compass. Help individuals understand and appreciate how pricing works, shedding a light on their pricing puzzles."}
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
