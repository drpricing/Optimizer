import streamlit as st
from groq import Client
import logging
import uuid
import requests
import base64
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API keys
groq_api_key = st.secrets["groq"]["api_key"]
github_token = st.secrets["github"]["token"]
repo_owner = "drpricing"
repo_name = "mylibrary"

# Initialize SentenceTransformer model for embeddings
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

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
        file_content = response.json().get("content")
        if file_content:
            try:
                decoded_content = base64.b64decode(file_content).decode('utf-8', errors='ignore')
                logging.info(f"Loaded {path} (Size: {len(decoded_content)} chars)")
                return decoded_content
            except Exception as e:
                logging.error(f"Error decoding {path}: {e}")
                return None
        else:
            logging.warning(f"No content found in {path}")
            return None
    else:
        logging.error(f"Error fetching {path} from GitHub: {response.status_code}")
        return None

# Load documents and create a FAISS index
documents_content = {}
document_snippets = []
document_metadata = []
index = faiss.IndexFlatL2(384)  # FAISS index for vector search (384-dimension vectors)

for path in file_paths:
    content = get_file_from_github(repo_owner, repo_name, path, github_token)
    if content:
        documents_content[path] = content
        # Split document into smaller passages
        paragraphs = content.split("\n\n")  # Split by double newline
        for para in paragraphs:
            if len(para) > 50:  # Ignore very short lines
                document_snippets.append(para)
                document_metadata.append(path)

# Convert all document snippets into embeddings
if document_snippets:
    embeddings = embedding_model.encode(document_snippets, convert_to_numpy=True)
    index.add(embeddings)  # Add embeddings to FAISS index
    logging.info(f"Added {len(document_snippets)} passages to FAISS index.")

# Function to retrieve the most relevant snippets
def retrieve_relevant_snippets(query, top_k=3):
    if not document_snippets:
        return ["No document data available."]
    
    query_embedding = embedding_model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for i in range(len(indices[0])):
        idx = indices[0][i]
        results.append(f"**Source: {document_metadata[idx]}**\n{document_snippets[idx]}\n")
    
    return results

# Function to get chatbot response
def get_pricing_advice(user_input):
    try:
        # Search private library using FAISS vector retrieval
        library_results = retrieve_relevant_snippets(user_input)
        library_context = "\n\n".join(library_results) if library_results else "No relevant documents found."

        logging.info(f"Library context:\n{library_context}")

        # Call Groq API
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, a pricing expert and author of 'The Pricing Puzzle' and 'The Pricing Compass'. You assist users in understanding pricing challenges."},
                {"role": "user", "content": f"User Query: {user_input}\n\nRelevant Information from Private Library:\n{library_context}"}
            ],
            temperature=0.7
        )

        api_response = response.choices[0].message.get("content", "No response received.")
        return api_response
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return f"Error: {str(e)}"

# Main chatbot logic
if __name__ == "__main__":
    if prompt := st.chat_input("Describe your pricing challenge:"):
        st.session_state["conversation"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = get_pricing_advice(prompt)
            message_placeholder.markdown(full_response)
            st.session_state["conversation"].append({"role": "assistant", "content": full_response})