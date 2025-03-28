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
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize session state with proper defaults
def initialize_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = [{
            "role": "assistant",
            "content": "Welcome to Dr. Pricing's ChatBot! I'm here to help you with your pricing challenges. Please describe your pricing question or challenge below."
        }]
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = str(uuid.uuid4())
    if "documents_loaded" not in st.session_state:
        st.session_state.documents_loaded = False
    if "document_snippets" not in st.session_state:
        st.session_state.document_snippets = []
    if "document_metadata" not in st.session_state:
        st.session_state.document_metadata = []

initialize_session_state()

# Load API keys from Streamlit secrets
try:
    groq_api_key = st.secrets["groq"]["api_key"]
    github_token = st.secrets["github"]["token"]
except Exception as e:
    st.error(f"Error loading secrets: {e}")
    st.stop()

repo_owner = "drpricing"
repo_name = "mylibrary"

# Initialize SentenceTransformer for embeddings
try:
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
except Exception as e:
    st.error(f"Error loading embedding model: {e}")
    st.stop()

# List of file paths to your library
file_paths = [
    "2020_Book_ThePricingPuzzle.pdf",
    "2024_Book_ThePricingCompass.pdf",
    "336421_Final proofs.pdf",
    "Book AI-Enabled Pricing_2025.pdf",
    "misc.docx",
    "Simon_Fassnacht-Reference+Document.pdf"
]

# Initialize Groq client
try:
    client = Groq(api_key=groq_api_key)
except Exception as e:
    st.error(f"Error initializing Groq client: {e}")
    st.stop()

# Function to fetch file from GitHub
def get_file_from_github(owner, repo, path, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        file_content = response.json().get("content")
        if file_content:
            try:
                decoded_content = base64.b64decode(file_content).decode('utf-8', errors='ignore')
                logger.info(f"Loaded {path} (Size: {len(decoded_content)} chars)")
                return decoded_content
            except Exception as e:
                logger.error(f"Error decoding {path}: {e}")
                return None
        else:
            logger.warning(f"No content found in {path}")
            return None
    except Exception as e:
        logger.error(f"Error fetching {path} from GitHub: {str(e)}")
        return None

# Load documents and create FAISS index if not already loaded
if not st.session_state.documents_loaded:
    with st.spinner("Loading documents..."):
        documents_content = {}
        all_snippets = []
        all_metadata = []

        for path in file_paths:
            content = get_file_from_github(repo_owner, repo_name, path, github_token)
            if content:
                documents_content[path] = content
                # Split document into smaller passages
                paragraphs = content.split("\n\n")  # Split by double newline
                for para in paragraphs:
                    if len(para.strip()) > 50:  # Ignore very short lines
                        all_snippets.append(para)
                        all_metadata.append(path)

        # Store in session state
        st.session_state.document_snippets = all_snippets
        st.session_state.document_metadata = all_metadata

        # Create FAISS index if we have documents
        if all_snippets:
            try:
                embeddings = embedding_model.encode(all_snippets, convert_to_numpy=True)
                index = faiss.IndexFlatL2(384)  # FAISS index for vector search
                index.add(embeddings)
                st.session_state.faiss_index = index
                logger.info(f"Added {len(all_snippets)} passages to FAISS index.")
            except Exception as e:
                st.error(f"Error creating embeddings: {e}")
                st.stop()

        st.session_state.documents_loaded = True

# Function to retrieve the most relevant snippets
def retrieve_relevant_snippets(query, top_k=3):
    if not st.session_state.document_snippets:
        return ["No document data available."]
    
    try:
        query_embedding = embedding_model.encode([query], convert_to_numpy=True)
        distances, indices = st.session_state.faiss_index.search(query_embedding, top_k)

        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx >= 0 and idx < len(st.session_state.document_snippets):  # Ensure index is valid
                results.append(
                    f"**Source: {st.session_state.document_metadata[idx]}**\n"
                    f"{st.session_state.document_snippets[idx]}\n"
                )
        
        return results if results else ["No relevant snippets found."]
    except Exception as e:
        logger.error(f"Error retrieving snippets: {e}")
        return [f"Error retrieving information: {str(e)}"]

# Function to get chatbot response
def get_pricing_advice(user_input):
    try:
        # Search private library using FAISS vector retrieval
        library_results = retrieve_relevant_snippets(user_input)
        library_context = "\n\n".join(library_results) if library_results else "No relevant documents found."

        logger.info(f"Library context:\n{library_context}")

        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are Dr. Pricing, a pricing expert and author of 'The Pricing Puzzle' and 'The Pricing Compass'. "
                              "You assist users in understanding pricing challenges. Use the provided context when relevant, "
                              "but don't mention it unless necessary."
                },
                {
                    "role": "user",
                    "content": f"User Query: {user_input}\n\nRelevant Information from Private Library:\n{library_context}"
                }
            ],
            temperature=0.7
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Groq API: {e}")
        return f"Sorry, I encountered an error processing your request. Please try again."

# Streamlit UI
st.title("💬 Dr. Pricing Talks")
st.caption("Powered by Groq and Llama3")

# Display conversation history
for message in st.session_state.conversation:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Describe your pricing challenge:"):
    # Add user message to conversation
    st.session_state.conversation.append({"role": "user", "content": prompt})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                response = get_pricing_advice(prompt)
                response_placeholder.markdown(response)
                st.session_state.conversation.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                response_placeholder.markdown(error_msg)
                st.session_state.conversation.append({"role": "assistant", "content": error_msg})