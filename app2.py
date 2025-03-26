import streamlit as st
from groq import Client
import logging
import uuid
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]
client = Client(api_key=groq_api_key)

# Load Google Drive credentials from Streamlit secrets
gcp_credentials = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_KEY"])
credentials = service_account.Credentials.from_service_account_info(
    gcp_credentials, scopes=["https://www.googleapis.com/auth/drive"]
)
drive_service = build("drive", "v3", credentials=credentials)

# Streamlit UI
st.title("💬 Dr. Pricing: Your Pricing Advisor")
st.write("Welcome to Dr. Pricing's Pricing Chat! Describe your pricing challenge below.")

# Initialize session state
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
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are Dr. Pricing, a pricing strategy expert. Help businesses adjust prices based on market conditions, competitor moves, cost shocks, and demand changes."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        return response.choices[0].message.get("content", "No response received.")
    except Exception as e:
        logging.error(f"Error calling Groq API: {e}")
        return f"Error: {str(e)}"

# Function to list Google Drive files
def list_drive_files():
    try:
        results = drive_service.files().list(pageSize=10, fields="files(id, name)").execute()
        files = results.get("files", [])
        return files
    except Exception as e:
        logging.error(f"Error accessing Google Drive: {e}")
        return []

# Function to read a file from Google Drive
def read_drive_file(file_id):
    try:
        request = drive_service.files().get_media(fileId=file_id)
        content = request.execute()
        return content.decode("utf-8")  # Assuming it's a text-based file
    except Exception as e:
        logging.error(f"Error reading file {file_id}: {e}")
        return "Could not retrieve file content."

# Display Google Drive files
st.subheader("📂 Access Google Drive Documents")
drive_files = list_drive_files()

if drive_files:
    file_options = {file["name"]: file["id"] for file in drive_files}
    selected_file = st.selectbox("Select a file to view:", list(file_options.keys()))

    if st.button("Open File"):
        file_content = read_drive_file(file_options[selected_file])
        st.text_area("File Content:", file_content, height=300)
else:
    st.write("No files found in Google Drive.")

# User input
if prompt := st.chat_input("Describe your pricing challenge:"):
    st.session_state["conversation"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    conversation_context = [
        {"role": "system", "content": "You are Dr. Pricing, a pricing strategy expert. Help businesses adjust prices based on market conditions, competitor moves, cost shocks, and demand changes."}
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
