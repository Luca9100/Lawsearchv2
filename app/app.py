import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st

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
st.set_page_config(page_title="Legal Bot", page_icon="⚖️")

st.title("Legal Bot - Search Swiss Laws")
st.write("Enter a query to search through the Swiss legal database.")

# Search bar
query = st.text_input("Enter your legal question or keywords:")

if query:
    # MongoDB query for matching documents
    results = collection.find({"text": {"$regex": query, "$options": "i"}})

    # Display results
    st.write(f"Results for: **{query}**")
    for result in results:
        st.subheader(result.get("title", "No Title"))
        st.write(f"**Law Name:** {result.get('law_name', 'Unknown')}")
        st.write(f"**Hierarchy:** {result.get('hierarchy', 'Unknown')}")
        st.write(result.get("text", "No Text Found"))
        st.write("---")
else:
    st.write("Use the search bar to find articles relevant to your query.")
