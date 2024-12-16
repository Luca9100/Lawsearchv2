import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient
import streamlit as st
from pydantic import BaseModel
from openai import OpenAI

# Load environment variables
load_dotenv('.env')

# MongoDB configuration
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = "legal_database_v2"
COLLECTION_NAME = "parsed_laws_v2"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# OpenAI configuration
api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=api_key)
model = "gpt-4"

# Load laws and buckets from laws.json
laws_file_path = 'laws.json'
with open(laws_file_path, 'r', encoding='utf-8') as file:
    laws_data = json.load(file)

base_url = laws_data.get("base_url", "")
laws = laws_data.get("laws", {})
buckets = laws_data.get("buckets", {})

# OpenAI interface messages based on language selection
openai_messages = {
    "de": {
        "first_interface_system": "Du bist ein Experte für Schweizer Recht und verweist in deinen Antworten, wann immer möglich, auf die relevanten Gesetze und Artikel.",
        "second_interface_system": "Du bist ein Experte für Schweizer Recht und extrahierst alle relevanten Gesetze und Artikel aus der query. Formatiere law_abbreviation_in_capitals so [OR, ZGB, DSG, HRegV, etc.] der gleiche Wert darf mehrfach in der Liste vorkommen. Formatiere art_number_formatted_as_eId so [art_4, art_620, art_635_a, etc.]"
    },
    "en": {
        "first_interface_system": "You are an expert in Swiss law and always refer to relevant laws and articles in your responses.",
        "second_interface_system": "You are an expert in Swiss law and extract all relevant laws and articles from the query. Format law_abbreviation_in_capitals as [CO, CC, CISA, AMLA, etc.]. The same value may appear multiple times in the list. Format art_number_formatted_as_eId as [art_4, art_620, art_635_a, etc.]."
    },
    "fr": {
        "first_interface_system": "Vous êtes un expert en droit suisse et vous faites toujours référence aux lois et articles pertinents dans vos réponses.",
        "second_interface_system": "Vous êtes un expert en droit suisse et vous extrayez toutes les lois et articles pertinents de la requête. Formatez law_abbreviation_in_capitals comme [CO, CC, LPD, LEFin, LPCC, LSFin, etc.]. La même valeur peut apparaître plusieurs fois dans la liste. Formatez art_number_formatted_as_eId comme [art_4, art_620, art_635_a, etc.]."
    },
    "it": {
        "first_interface_system": "Sei un esperto di diritto svizzero e fai sempre riferimento alle leggi e agli articoli pertinenti nelle tue risposte.",
        "second_interface_system": "Sei un esperto di diritto svizzero e estrai tutte le leggi e gli articoli pertinenti dalla richiesta. Format law_abbreviation_in_capitals come [CO, CC, LPD, LEFin, LPCC, LSFin, etc.]. Lo stesso valore può apparire più volte nell'elenco. Format art_number_formatted_as_eId come [art_4, art_620, art_635_a, etc.]."
    }
}

# Streamlit Configuration
st.set_page_config(page_title="Legal Bot Chat", page_icon="💬")

st.title("Legal Bot - Chat with Swiss Laws")
st.write("Ask questions and get answers based on the legal database.")

# Add language selection to the sidebar
st.sidebar.header("Select Language")
language = st.sidebar.selectbox("Language", options=["de", "en", "fr", "it"], index=0)

# Add bucket overview to the sidebar
st.sidebar.header("Buckets Overview")
for bucket_name, laws_by_language in buckets.items():
    laws_for_selected_language = laws_by_language.get(language, [])
    st.sidebar.markdown(f"**{bucket_name} ({language.upper()})**: {', '.join(laws_for_selected_language)}")

# Add checkboxes for bucket selection
st.sidebar.header("Filter by Buckets")
selected_buckets = [
    bucket_name
    for bucket_name, laws_by_language in buckets.items()
    if st.sidebar.checkbox(bucket_name, value=True)
]

# Map selected buckets to language-specific laws
selected_laws = []
for bucket_name in selected_buckets:
    selected_laws.extend(buckets[bucket_name].get(language, []))

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
                # Prepare unique list of laws
                unique_laws = list(set(selected_laws))  # Remove duplicates
                laws_list_str = ', '.join(unique_laws)  # Convert to a comma-separated string

                # Dynamically format the system message for the first interface
                first_system_message = (
                    f"{openai_messages[language]['first_interface_system']} "
                    f"Pay special attention to the following laws: {laws_list_str}."
                )

                # First Interface: OpenAI ChatGPT Response
                completion = openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": first_system_message},
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
                        {"role": "system", "content": openai_messages[language]["second_interface_system"]},
                        {"role": "user", "content": response},
                    ],
                    response_format=LawRetrieval,
                )
                law_extraction = extraction.choices[0].message.parsed

                # Map extracted laws to exact casing in laws.json
                exact_case_laws = [law for law in law_extraction.law_abbreviation_in_capitals if law in laws.keys()]

                # Query MongoDB Database
                mongo_query = {
                    "law_name": {"$regex": f"^({'|'.join(law_extraction.law_abbreviation_in_capitals)})$", "$options": "i"}, #search the law name case insensitive to retrieve laws like HRegV
                    "eId": {"$in": law_extraction.art_number_formatted_as_eId},
                    "bucket": {"$in": selected_buckets},
                    "language": language
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
