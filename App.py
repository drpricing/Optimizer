import streamlit as st
import groq

# Load API key from Streamlit secrets
groq_api_key = st.secrets["groq"]["api_key"]

# Initialize Groq client
client = groq.Client(api_key=groq_api_key)

# Streamlit UI
st.title("💰 Price Adjustment Advisor Chatbot")
st.write("Describe your pricing challenge, and I'll suggest an adjustment.")

# User input
user_input = st.text_area("Enter details about your product and pricing challenge:")

# Function to call Groq API
def get_pricing_advice(user_input):
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a pricing strategy expert. Help businesses adjust prices based on market conditions, competitor moves, cost shocks, and demand changes."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Button to get recommendation
if st.button("Get Pricing Advice"):
    if user_input.strip():
        with st.spinner("Analyzing pricing strategy..."):
            advice = get_pricing_advice(user_input)
        st.subheader("💡 Pricing Recommendation:")
        st.write(advice)
    else:
        st.warning("Please enter details about your pricing challenge.")
