import os
import shutil
import json
from fetch_laws import fetch_laws  # Assuming fetch_laws.py is in the same directory
from xmlparser import parse_law_file  # Assuming xmlparser handles generic laws
from xmlparserORandZGB import parse_or_zgb_file  # Assuming this handles OR and ZGB
from config import collection

# Load laws and buckets from laws.json
def load_laws_and_buckets():
    """
    Loads laws and buckets from laws.json.
    """
    json_path = os.path.join(os.path.dirname(__file__), "laws.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("laws.json not found. Please create it with the laws and buckets.")
    with open(json_path, "r") as f:
        data = json.load(f)
        return data["laws"], data["buckets"]

laws_by_language, buckets = load_laws_and_buckets()
laws_folder = os.path.join(os.path.dirname(__file__), "laws")

def clear_database():
    """Delete all entries in the current MongoDB collection."""
    collection.delete_many({})
    print("Cleared the existing database.")

def delete_laws_folder():
    """Delete the current 'laws' folder and all its contents."""
    if os.path.exists(laws_folder):
        shutil.rmtree(laws_folder)
        print(f"Deleted the folder: {laws_folder}")
    else:
        print(f"Laws folder '{laws_folder}' does not exist. Skipping deletion.")

def build_bucket_law_mapping():
    """
    Build a mapping of laws to their associated buckets per language.
    Example:
        {
            "de": {"OR": ["General Counsel Law", "Corporate Law", "Financial Law"], ...},
            "en": {"CO": ["General Counsel Law", "Corporate Law"], ...},
            "fr": {"CO": ["General Counsel Law", "Corporate Law"], ...}
        }
    """
    bucket_law_mapping = {lang: {} for lang in laws_by_language.keys()}

    for bucket_name, laws_per_language in buckets.items():
        for lang, laws in laws_per_language.items():
            for law in laws:
                if law not in bucket_law_mapping[lang]:
                    bucket_law_mapping[lang][law] = []
                bucket_law_mapping[lang][law].append(bucket_name)

    return bucket_law_mapping

def build_database():
    """
    Fetch laws, parse them, and populate the database for all supported languages.
    """
    # Clear existing database
    clear_database()

    # Delete laws folder
    delete_laws_folder()

    # Fetch new laws
    print("Fetching new laws...")
    fetch_laws()

    # Build the bucket-law mapping
    bucket_law_mapping = build_bucket_law_mapping()

    # Supported languages
    languages = ["de", "en", "fr"]

    # Parse and write laws to the database for each language
    print("Building the database...")
    for language in languages:
        print(f"Processing language: {language}")
        for law, buckets in bucket_law_mapping[language].items():
            # Construct file path for the current law
            file_path = os.path.join(laws_folder, language, f"{law}.xml")
            if os.path.exists(file_path):
                # Determine parsing method based on law
                if law in ["OR", "ZGB", "CO", "CC"]:
                    parsed_data = parse_or_zgb_file(file_path, language)
                else:
                    parsed_data = parse_law_file(file_path, law, language)

                # Add bucket information to parsed articles
                for article in parsed_data:
                    article["bucket"] = buckets  # Assign all relevant buckets

                # Insert articles into the database
                if parsed_data:
                    collection.insert_many(parsed_data)
                    print(f"Inserted {len(parsed_data)} articles for {law} ({language}) with buckets {buckets}.")
            else:
                print(f"File {file_path} for {law} ({language}) not found.")

if __name__ == "__main__":
    build_database()
