import streamlit as st
from groq import Groq
import requests
import base64
from io import BytesIO
import os

# Ensure required libraries are available
try:
    from PyPDF2 import PdfReader
except ImportError:
    st.warning("PyPDF2 not installed. PDF extraction may fail.")

try:
    from docx import Document
except ImportError:
    st.warning("python-docx not installed. DOCX extraction may fail.")

# --- Private Library Configuration ---
github_token = st.secrets["github"]["token"]
repo_owner = "drpricing"
repo_name = "mylibrary"

file_paths = [
    "misc1.docx"
    # Add or remove files as needed.
]

# --- File Processing Functions ---

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF files."""
    text = ""
    try:
        pdf_stream = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        for page in reader.pages:
            extracted_text = page.extract_text() or ""
            text += extracted_text + "\n"
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
    return text.strip()

def extract_text_from_docx(docx_bytes):
    """Extract text from DOCX files."""
    text = ""
    try:
        doc_stream = BytesIO(docx_bytes)
        doc = Document(doc_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        st.error(f"Error extracting DOCX text: {e}")
    return text.strip()

def fetch_file_content(path):
    """Fetch file from GitHub and extract text if possible."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    headers = {"Authorization": f"token {github_token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("encoding") == "base64":
            try:
                decoded_bytes = base64.b64decode(data["content"])
                ext = os.path.splitext(path)[1].lower()
                if ext == ".pdf":
                    return extract_text_from_pdf(decoded_bytes)
                elif ext == ".docx":
                    return extract_text_from_docx(decoded_bytes)
                else:
                    return decoded_bytes.decode('utf-8', errors='ignore')
            except Exception as e:
                st.error(f"Error decoding {path}: {e}")
    else:
        st.error(f"Failed to fetch {path} (HTTP {response.status_code})")
    return None

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm Dr. Pricing. How can I help with your pricing questions today?"
    }]

# --- Initialize the Groq Client ---
try:
    api_key = st.secrets["groq"]["api_key"]
    client = Groq(api_key=api_key)
except Exception as err:
    st.error(f"Failed to initialize Groq client: {err}")
    st.stop()

# --- Streamlit UI Setup ---
st.title("💬 Dr. Pricing Talks")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- Handle User Input ---
user_input = st.chat_input("Ask about pricing...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    # --- Fetch Information from Private Library (Append Full File Content) ---
    library_context = ""
    for path in file_paths:
        file_content = fetch_file_content(path)
        if file_content:
            library_context += f"From {os.path.basename(path)}:\n{file_content}\n\n"
    
    # Optionally, display the library context to the user
    if library_context:
        with st.expander("Library Context"):
            st.write(library_context)
    
    # --- Construct the Payload ---
    messages_payload = [
        {"role": "system", "content": "You are Dr. Pricing, a pricing expert. Answer concisely."}
    ]
    
    messages_payload.append({
        "role": "system",
        "content": f"Context from private library:\n{library_context}"
    })
    
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
