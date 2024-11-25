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

# Define buckets and associated laws
buckets = {
    "General Counsel Law": ["OR", "ZGB", "DSG"],
    "Corporate Law": ["OR", "ZGB"],
    "Financial Law": ["OR", "ZGB", "FINIG", "KAG", "FIDLEG", "GwG", "BankG"]
}

# Streamlit Configuration
st.set_page_config(page_title="Legal Bot", page_icon="⚖️")

st.title("Legal Bot - Search Swiss Laws")
st.write("Enter a query to search through the Swiss legal database.")

# Add collapsible dropdown for bucket overview
with st.sidebar.expander("Buckets Overview", expanded=False):
    for bucket_name, laws in buckets.items():
        st.markdown(f"**{bucket_name}**: {', '.join(laws)}")

# Add checkboxes for bucket selection
st.sidebar.header("Filter by Buckets")
general_counsel = st.sidebar.checkbox("General Counsel Law", value=True)
corporate = st.sidebar.checkbox("Corporate Law", value=True)
financial = st.sidebar.checkbox("Financial Law", value=True)

# Collect selected buckets
selected_buckets = []
if general_counsel:
    selected_buckets.append("General Counsel Law")
if corporate:
    selected_buckets.append("Corporate Law")
if financial:
    selected_buckets.append("Financial Law")

# Show the query bar
query = st.text_input("Enter your legal question or keywords:")


if query:
    if not selected_buckets:
        st.warning("Please select at least one bucket to search in.")
    else:
        
        with st.spinner("Searching the legal database..."):
            # MongoDB query for matching documents and filtering by bucket
            results = list(
                collection.find(
                    {
                        "text": {"$regex": query, "$options": "i"},
                        "bucket": {"$elemMatch": {"$in": selected_buckets}},
                    }
                )
            )
            
        if results:
            st.write(f"Results for: **{query}**")
            for result in results:
                # Extract Article Number from eId
                article_number = result.get("eId", "Unknown").split("_", 1)[-1]

                st.subheader(result.get("title", "No Title"))
                st.write(f"**Law Name:** {result.get('law_name', 'Unknown')}")
                st.write(f"**Article Number:** {article_number}")
                st.write(f"**Buckets:** {', '.join(result.get('bucket', []))}")
                st.markdown(f"[Go to Article]({result.get('link', '#')})", unsafe_allow_html=True)

                # Display the full text of the article
                st.write(result.get("text", "No Text Found"))
                st.write("---")
        else:
            st.warning("No results found for your query. Please try different keywords.")
else:
    st.write("Use the search bar to find articles relevant to your query.")
