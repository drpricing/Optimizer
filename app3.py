import streamlit as st
from groq import Groq
import logging
import uuid
import requests
import base64
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state with proper defaults
def initialize_session_state():
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.conversation = [{
            "role": "assistant", 
            "content": "Welcome to Dr. Pricing's ChatBot! I can help with pricing strategy questions. What would you like to know?"
        }]
        st.session_state.conversation_id = str(uuid.uuid4())
        st.session_state.documents_loaded = False
        st.session_state.document_snippets = []
        st.session_state.document_metadata = []
        st.session_state.faiss_index = None

initialize_session_state()

# Load API keys from Streamlit secrets
try:
    groq_api_key = st.secrets["groq"]["api_key"]
    github_token = st.secrets["github"]["token"]
except Exception as e:
    st.error(f"Error loading secrets: {e}")
    st.stop()

# Initialize components
@st.cache_resource(show_spinner=False)
def load_embedding_model():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

try:
    embedding_model = load_embedding_model()
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Initialization error: {e}")
    st.stop()

# Document loading and processing
def load_documents():
    if st.session_state.documents_loaded:
        return

    repo_owner = "drpricing"
    repo_name = "mylibrary"
    file_paths = [
        "2020_Book_ThePricingPuzzle.pdf",
        "2024_Book_ThePricingCompass.pdf",
        "336421_Final proofs.pdf",
        "Book AI-Enabled Pricing_2025.pdf",
        "misc.docx",
        "Simon_Fassnacht-Reference+Document.pdf"
    ]

    all_snippets = []
    all_metadata = []

    for path in file_paths:
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
            response = requests.get(url, headers={"Authorization": f"token {github_token}"}, timeout=10)
            response.raise_for_status()
            
            content = response.json().get("content")
            if content:
                decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
                paragraphs = [p.strip() for p in decoded.split('\n\n') if len(p.strip()) > 50]
                all_snippets.extend(paragraphs)
                all_metadata.extend([path] * len(paragraphs))
        except Exception as e:
            logger.warning(f"Skipping {path}: {str(e)}")

    if all_snippets:
        try:
            embeddings = embedding_model.encode(all_snippets, convert_to_numpy=True)
            index = faiss.IndexFlatL2(384)
            index.add(embeddings)
            st.session_state.faiss_index = index
            st.session_state.document_snippets = all_snippets
            st.session_state.document_metadata = all_metadata
        except Exception as e:
            logger.error(f"Indexing failed: {e}")

    st.session_state.documents_loaded = True

# Start document loading in background
if not st.session_state.documents_loaded:
    with st.spinner("Loading knowledge base..."):
        load_documents()

# Chat functions
def get_pricing_advice(user_input):
    try:
        # For simple greetings, respond immediately without document search
        if user_input.lower().strip() in {"hi", "hello", "hey"}:
            return "Hello! I'm Dr. Pricing's assistant. How can I help with your pricing questions today?"
        
        # For other queries, use document search if available
        library_context = ""
        if st.session_state.faiss_index:
            try:
                query_embedding = embedding_model.encode([user_input], convert_to_numpy=True)
                distances, indices = st.session_state.faiss_index.search(query_embedding, 3)
                
                relevant = []
                for idx in indices[0]:
                    if 0 <= idx < len(st.session_state.document_snippets):
                        relevant.append(
                            f"From {st.session_state.document_metadata[idx]}:\n"
                            f"{st.session_state.document_snippets[idx]}\n"
                        )
                library_context = "\n".join(relevant) if relevant else ""
            except Exception as e:
                logger.warning(f"Document search failed: {e}")

        # Call Groq API
        messages = [
            {"role": "system", "content": "You're Dr. Pricing, a pricing expert. Answer concisely."},
            {"role": "user", "content": user_input}
        ]
        
        if library_context:
            messages.insert(1, {
                "role": "system", 
                "content": f"Relevant context:\n{library_context}\nUse this if helpful."
            })

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.7,
            timeout=10
        )
        
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"API Error: {e}")
        return "I encountered a technical issue. Please try your question again."

# Streamlit UI
st.title("💬 Dr. Pricing Assistant")
st.caption("Expert pricing advice at your fingertips")

# Display chat
for msg in st.session_state.conversation:
    st.chat_message(msg["role"]).write(msg["content"])

# User input
if prompt := st.chat_input("Ask about pricing strategies..."):
    st.session_state.conversation.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_pricing_advice(prompt)
            st.write(response)
            st.session_state.conversation.append({"role": "assistant", "content": response})