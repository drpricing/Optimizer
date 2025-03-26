import streamlit as st
import requests

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Groq API endpoint
GROQ_API_URL = "https://api.groq.com/v1/chat/completions"

# Streamlit UI
st.title("💰 Price Adjustment Advisor Chatbot")
st.write("Describe your pricing challenge, and I'll suggest an adjustment.")

# User input
user_input = st.text_area("Enter details about your product and pricing challenge:")

# Function to call Groq API
def get_pricing_advice(user_input):
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a pricing strategy expert helping businesses optimize their prices. Consider market factors, cost changes, demand shifts, and competitive pricing."},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.7
    }
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.json()}"

# Button to get recommendation
if st.button("Get Pricing Advice"):
    if user_input.strip():
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        st.subheader("💡 Pricing Recommendation:")
        st.write(advice)
    else:
        st.warning("Please enter details about your pricing challenge.")
