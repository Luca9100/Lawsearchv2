import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st
from pydantic import BaseModel
from openai import OpenAI

# Load environment variables
load_dotenv('/Users/luca/Desktop/Law_Bot_2.0/.env')

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "legal_database"
COLLECTION_NAME = "parsed_laws"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# OpenAI configuration
api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)
model = "gpt-4"

# Define buckets and associated laws
buckets = {
    "General Counsel Law": ["OR", "ZGB", "DSG"],
    "Corporate Law": ["OR", "ZGB"],
    "Financial Law": ["OR", "ZGB", "FINIG", "KAG", "FIDLEG", "GwG", "BankG"]
}

# Streamlit Configuration
st.set_page_config(page_title="Legal Bot Chat", page_icon="💬")

st.title("Legal Bot - Chat with Swiss Laws")
st.write("Ask questions and get answers based on the legal database.")

# Add bucket overview to the sidebar
st.sidebar.header("Buckets Overview")
for bucket_name, laws in buckets.items():
    st.sidebar.markdown(f"**{bucket_name}**: {', '.join(laws)}")

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

# Initialize chat messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])

# User input
if user_input := st.chat_input("Ask a legal question..."):
    # Add user message to session
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)

    if not selected_buckets:
        st.session_state.messages.append(
            {"role": "assistant", "content": "Please select at least one bucket to search in."}
        )
        st.chat_message("assistant").markdown("Please select at least one bucket to search in.")
    else:
        with st.spinner("Processing your question..."):
            try:
                # First Interface: OpenAI ChatGPT Response
                completion = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Du bist ein Experte für Schweizer Recht und verweist in deinen Antworten, wann immer möglich, auf die relevanten Gesetze und Artikel."},
                        {"role": "user", "content": user_input},
                    ],
                )
                response = completion.choices[0].message.content  # Extract content properly

                # Add the assistant's response to the chat
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.chat_message("assistant").markdown(response)

                # Second Interface: Extract Laws and Articles
                class LawRetrieval(BaseModel):
                    law_abbreviation_in_capitals: list[str]
                    art_number_formatted_as_eId: list[str]

                extraction = openai_client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    messages=[
                        {"role": "system", "content": "Du bist ein Experte für Schweizer Recht und extrahierst alle relevanten Gesetze und Artikel aus der query. Formatiere law_abbreviation_in_capitals so [OR, ZGB, OR, DSG, OR, etc.] der gleiche Wert darf mehrfach in der Liste vorkommen. Formatiere art_number_formatted_as_eId so [art_4, art_620, art_635_a, etc.]"},
                        {"role": "user", "content": response},
                    ],
                    response_format=LawRetrieval,
                )
                law_extraction = extraction.choices[0].message.parsed

                # Query MongoDB Database
                mongo_query = {
                    "law_name": {"$in": law_extraction.law_abbreviation_in_capitals},
                    "eId": {"$in": law_extraction.art_number_formatted_as_eId},
                    "bucket": {"$in": selected_buckets},  # Match string bucket values
                }
                results = list(collection.find(mongo_query))

                # Display Results
                if results:
                    st.write("### Relevant Articles from the Database")
                    for result in results:
                        article_number = result.get("eId", "Unknown").split("_", 1)[-1]

                        st.subheader(result.get("title", "No Title"))
                        st.write(f"**Law Name:** {result.get('law_name', 'Unknown')}")
                        st.write(f"**Article Number:** {article_number}")
                        
                        # Ensure proper display of bucket
                        bucket_value = result.get("bucket", "Unknown")
                        if isinstance(bucket_value, list):
                            st.write(f"**Buckets:** {', '.join(bucket_value)}")
                        else:
                            st.write(f"**Buckets:** {bucket_value}")
                        
                        st.markdown(f"[Go to Article]({result.get('link', '#')})", unsafe_allow_html=True)
                        st.write(result.get("text", "No Text Found"))
                        st.write("---")
                else:
                    st.warning("No relevant legal articles found for your query.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
