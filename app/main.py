import os
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st
import openai

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
            # Query MongoDB for relevant articles filtered by buckets
            results = list(
                collection.find(
                    {
                        "text": {"$regex": user_input, "$options": "i"},
                        "bucket": {"$elemMatch": {"$in": selected_buckets}},
                    }
                )
            )

            if results:
                # Prepare legal articles for context
                context = "\n\n".join(
                    [
                        f"{res.get('title', 'No Title')} ({', '.join(res.get('bucket', []))}):\n"
                        f"{res.get('text', '')}"
                        for res in results
                    ]
                )

                # Send query to OpenAI
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a legal assistant for Swiss laws."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_input}"},
                    ],
                )

                # Get the assistant's response
                assistant_reply = response["choices"][0]["message"]["content"]
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                st.chat_message("assistant").markdown(assistant_reply)
            else:
                no_results_message = "No relevant legal articles found for your query."
                st.session_state.messages.append({"role": "assistant", "content": no_results_message})
                st.chat_message("assistant").markdown(no_results_message)
