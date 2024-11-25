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

# Streamlit Configuration
st.set_page_config(page_title="Legal Bot Chat", page_icon="💬")

st.title("Legal Bot - Chat with Swiss Laws")
st.write("Ask questions and get answers based on the legal database.")

# Chat interface
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

    # Query MongoDB for relevant articles
    results = collection.find({"text": {"$regex": user_input, "$options": "i"}})

    # Prepare legal articles for context
    context = "\n\n".join(
        [f"{res.get('title', 'No Title')}: {res.get('text', '')}" for res in results]
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
