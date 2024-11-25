import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st
import time

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "legal_database"
COLLECTION_NAME = "parsed_laws"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Streamlit Configuration
st.set_page_config(page_title="Test Spinner - Legal Bot", page_icon="⚙️")

st.title("Testing Spinner in Legal Bot")
st.write("This is a test version to ensure the spinner works as expected.")

# Search bar
query = st.text_input("Enter a test query:")

if query:
    with st.spinner("Simulating search..."):
        time.sleep(2)  # Artificial delay for testing the spinner
        # Simulated results for testing
        results = [{"title": "Test Title", "law_name": "Test Law", "text": "Test Content"}]

    if results:
        st.write(f"Results for: **{query}**")
        for result in results:
            st.subheader(result.get("title", "No Title"))
            st.write(f"**Law Name:** {result.get('law_name', 'Unknown')}")
            st.write(result.get("text", "No Text Found"))
            st.write("---")
    else:
        st.warning("No results found for your test query.")
else:
    st.write("Use the search bar to simulate searching.")

