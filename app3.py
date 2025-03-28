import streamlit as st
from groq import Groq
import logging
import uuid
import requests
import base64
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if "conversation" not in st.session_state:
    st.session_state.conversation = [{
        "role": "assistant",
        "content": "Hello! I'm Dr. Pricing's AI assistant. How can I help with your pricing questions today?"
    }]
    st.session_state.documents_loaded = False

# Load only essential documents
file_paths = [
    "2020_Book_ThePricingPuzzle.pdf",
    "2024_Book_ThePricingCompass.pdf",
    "Book AI-Enabled Pricing_2025.pdf",
    "misc.docx"
]

# Load API keys
try:
    groq_api_key = st.secrets["groq"]["api_key"]
    github_token = st.secrets["github"]["token"]
except Exception as e:
    st.error(f"Configuration error: {e}")
    st.stop()

# Initialize Groq client (fast)
try:
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}")
    st.stop()

# Load embedding model with caching
@st.cache_resource
def load_embeddings():
    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

embedding_model = load_embeddings()

# Streamlit UI
st.title("💬 Dr. Pricing Assistant")
st.caption("Instant pricing expertise")

# Display chat history
for msg in st.session_state.conversation:
    st.chat_message(msg["role"]).write(msg["content"])

# Document loading (only once, in background)
if not st.session_state.documents_loaded:
    with st.spinner("Loading knowledge base (one-time process)..."):
        try:
            documents = []
            metadata = []
            
            for path in file_paths:
                try:
                    url = f"https://api.github.com/repos/drpricing/mylibrary/contents/{path}"
                    response = requests.get(url, headers={"Authorization": f"token {github_token}"}, timeout=15)
                    response.raise_for_status()
                    
                    content = base64.b64decode(response.json()["content"]).decode('utf-8', errors='ignore')
                    paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
                    documents.extend(paragraphs)
                    metadata.extend([path] * len(paragraphs))
                except Exception as e:
                    logger.warning(f"Skipped {path}: {e}")
                    continue
            
            if documents:
                embeddings = embedding_model.encode(documents, convert_to_numpy=True)
                index = faiss.IndexFlatL2(384)
                index.add(embeddings)
                st.session_state.faiss_index = index
                st.session_state.document_snippets = documents
                st.session_state.document_metadata = metadata
            
            st.session_state.documents_loaded = True
        except Exception as e:
            logger.error(f"Document loading failed: {e}")
            st.session_state.documents_loaded = True  # Mark as loaded anyway to prevent retries

# Chat function
def get_response(user_input):
    try:
        # Handle simple greetings immediately
        if user_input.lower().strip() in {"hi", "hello", "hey"}:
            return "Hello! How can I assist with your pricing questions today?"
        
        # Prepare context from documents if available
        context = ""
        if st.session_state.get('faiss_index'):
            try:
                query_embedding = embedding_model.encode([user_input], convert_to_numpy=True)
                _, indices = st.session_state.faiss_index.search(query_embedding, 2)
                
                relevant_info = []
                for idx in indices[0]:
                    if 0 <= idx < len(st.session_state.document_snippets):
                        relevant_info.append(
                            f"From {st.session_state.document_metadata[idx]}:\n"
                            f"{st.session_state.document_snippets[idx]}\n"
                        )
                context = "\n".join(relevant_info) if relevant_info else ""
            except Exception as e:
                logger.warning(f"Document search error: {e}")

        # Call LLM
        messages = [{"role": "system", "content": "You're Dr. Pricing, a pricing expert. Be concise and helpful."}]
        if context:
            messages.append({"role": "system", "content": f"Relevant context:\n{context}"})
        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.7,
            timeout=10
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Response error: {e}")
        return "I encountered a minor issue. Could you please rephrase your question?"

# Handle user input
if prompt := st.chat_input("Ask about pricing..."):
    st.session_state.conversation.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_response(prompt)
            st.write(response)
            st.session_state.conversation.append({"role": "assistant", "content": response})