import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st
import openai
from pydantic import BaseModel

# Load environment variables explicitly
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
openai.api_key = os.getenv("OPENAI_API_KEY")
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
                # First: Get GPT-4 response
                gpt_response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a legal assistant for Swiss laws."},
                        {"role": "user", "content": user_input},
                    ],
                )
                assistant_reply = gpt_response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.chat_message("assistant").markdown(assistant_reply)

                # Second: Extract relevant laws and articles using function-like schema
                class LawRetrieval(BaseModel):
                    law_abbreviation_in_capitals: list[str]
                    art_number_formatted_as_eId: list[str]

                extraction_tool = openai.pydantic_function_tool(LawRetrieval)

                extraction_response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a legal assistant for Swiss laws."},
                        {"role": "user", "content": assistant_reply},
                    ],
                    tools=[extraction_tool],
                )

                law_extraction = extraction_response.choices[0].message.tool_calls[0].function.arguments
                st.write("Extracted Law Information:")
                st.json(law_extraction)

                # Third: Query MongoDB for articles based on extracted laws
                extracted_laws = law_extraction["law_abbreviation_in_capitals"]
                extracted_articles = law_extraction["art_number_formatted_as_eId"]

                # Build MongoDB query
                query = {
                    "$or": [
                        {"law_name": law, "eId": article}
                        for law, article in zip(extracted_laws, extracted_articles)
                    ]
                }

                # Retrieve articles
                mongo_results = list(collection.find(query))

                if mongo_results:
                    st.write("Relevant Articles:")
                    for result in mongo_results:
                        st.subheader(result.get("title", "No Title"))
                        st.write(f"**Law Name:** {result.get('law_name', 'Unknown')}")
                        st.write(f"**Article Number:** {result.get('eId', 'Unknown')}")
                        st.write(f"**Buckets:** {', '.join(result.get('bucket', []))}")
                        st.markdown(f"[Go to Article]({result.get('link', '#')})", unsafe_allow_html=True)
                        st.write(result.get("text", "No Text Found"))
                        st.write("---")
                else:
                    st.write("No relevant articles found for the extracted information.")

            except Exception as e:
                st.error(f"An error occurred: {e}")
